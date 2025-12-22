"""
Model training script for STModel service.
Run this separately to train the model on historical data.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, random_split
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler
import os

# Import the model from app.py
from app import WaterQualityPredictor

def create_synthetic_data(n_samples=5000, seq_length=24, n_features=5, n_targets=3):
    """
    Create synthetic training data that mimics real sensor patterns.
    In a real scenario, replace this with loading from a database.
    """
    print(f"Generating {n_samples} synthetic training samples...")
    
    # Create time series with some seasonality and trends
    np.random.seed(42)
    
    # Features: temperature, ph, turbidity, conductivity, dissolved_oxygen
    X = np.zeros((n_samples, seq_length, n_features))
    y = np.zeros((n_samples, n_targets))
    
    for i in range(n_samples):
        # Base values with some station-specific variation
        base_temp = 20 + np.random.uniform(-5, 5)
        base_ph = 7.0 + np.random.uniform(-0.5, 0.5)
        base_turbidity = 15 + np.random.uniform(-5, 10)
        
        # Create time series with daily patterns
        for t in range(seq_length):
            daily_cycle = np.sin(2 * np.pi * t / 24)  # Daily cycle
            
            X[i, t, 0] = base_temp + daily_cycle * 3 + np.random.normal(0, 0.5)  # Temperature
            X[i, t, 1] = base_ph + daily_cycle * 0.1 + np.random.normal(0, 0.05)  # pH
            X[i, t, 2] = max(0, base_turbidity + daily_cycle * 5 + np.random.normal(0, 2))  # Turbidity
            X[i, t, 3] = 500 + daily_cycle * 100 + np.random.normal(0, 50)  # Conductivity
            X[i, t, 4] = 8 + daily_cycle * 1 + np.random.normal(0, 0.3)  # Dissolved oxygen
        
        # Targets: next values for ph, turbidity, temperature
        y[i, 0] = X[i, -1, 1] + np.random.normal(0, 0.1)  # Next pH
        y[i, 1] = X[i, -1, 2] + np.random.normal(0, 1)    # Next turbidity
        y[i, 2] = X[i, -1, 0] + np.random.normal(0, 0.5)  # Next temperature
    
    return X, y

def prepare_dataloaders(X, y, batch_size=32, train_ratio=0.8):
    """Prepare training and validation dataloaders."""
    dataset = TensorDataset(
        torch.FloatTensor(X),
        torch.FloatTensor(y)
    )
    
    # Split dataset
    train_size = int(train_ratio * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = random_split(dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    return train_loader, val_loader

def train_model():
    """Main training function."""
    print("Starting model training...")
    
    # Create synthetic data
    X, y = create_synthetic_data()
    
    # Create scalers for features and targets
    feature_scaler = StandardScaler()
    target_scaler = StandardScaler()
    
    # Reshape for scaling (samples*timesteps, features)
    X_reshaped = X.reshape(-1, X.shape[-1])
    feature_scaler.fit(X_reshaped)
    
    # Scale features
    X_scaled = feature_scaler.transform(X_reshaped).reshape(X.shape)
    
    # Scale targets
    y_scaled = target_scaler.fit_transform(y)
    
    # Save scalers for later use
    os.makedirs("./models", exist_ok=True)
    joblib.dump(feature_scaler, "./models/feature_scaler.pkl")
    joblib.dump(target_scaler, "./models/target_scaler.pkl")
    print("Scalers saved to ./models/")
    
    # Prepare dataloaders
    train_loader, val_loader = prepare_dataloaders(X_scaled, y_scaled)
    
    # Initialize model, loss function, and optimizer
    model = WaterQualityPredictor(
        input_features=X.shape[-1],
        hidden_size=64,
        output_features=y.shape[-1]
    )
    
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # Training loop
    num_epochs = 20
    train_losses = []
    val_losses = []
    
    for epoch in range(num_epochs):
        # Training phase
        model.train()
        train_loss = 0.0
        
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            predictions = model(batch_X)
            loss = criterion(predictions, batch_y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        
        avg_train_loss = train_loss / len(train_loader)
        train_losses.append(avg_train_loss)
        
        # Validation phase
        model.eval()
        val_loss = 0.0
        
        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                predictions = model(batch_X)
                loss = criterion(predictions, batch_y)
                val_loss += loss.item()
        
        avg_val_loss = val_loss / len(val_loader)
        val_losses.append(avg_val_loss)
        
        print(f"Epoch {epoch+1:02d}/{num_epochs} | "
              f"Train Loss: {avg_train_loss:.4f} | "
              f"Val Loss: {avg_val_loss:.4f}")
    
    # Save the trained model
    model_path = "./models/water_quality_predictor.pth"
    torch.save(model.state_dict(), model_path)
    print(f"\nTraining completed. Model saved to {model_path}")
    
    # Plot training history (optional)
    try:
        import matplotlib.pyplot as plt
        plt.figure(figsize=(10, 5))
        plt.plot(train_losses, label='Training Loss')
        plt.plot(val_losses, label='Validation Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.title('Training History')
        plt.legend()
        plt.grid(True)
        plt.savefig('./models/training_history.png')
        print("Training plot saved to ./models/training_history.png")
    except ImportError:
        print("Matplotlib not installed. Skipping plot generation.")
    
    return model

if __name__ == "__main__":
    # Train the model
    trained_model = train_model()
    
    # Test with a sample prediction
    print("\nTesting with sample data...")
    sample_input = torch.randn(1, 24, 5)  # Batch of 1, 24 timesteps, 5 features
    trained_model.eval()
    with torch.no_grad():
        sample_output = trained_model(sample_input)
    print(f"Sample input shape: {sample_input.shape}")
    print(f"Sample output shape: {sample_output.shape}")
    print(f"Sample prediction: {sample_output.numpy()[0]}")