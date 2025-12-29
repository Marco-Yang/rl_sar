#!/usr/bin/env python3
"""
Export Isaac Lab trained model to TorchScript format for C++ inference.

This script reconstructs the actor network from a checkpoint and exports it as TorchScript.
"""

import torch
import torch.nn as nn
import argparse
import os
import sys

class ActorNetwork(nn.Module):
    """
    Actor network for RL policy.
    Standard MLP architecture used in RSL_RL.
    """
    def __init__(self, num_obs: int, num_actions: int, hidden_dims: list = [512, 256, 128]):
        super().__init__()
        
        layers = []
        input_dim = num_obs
        
        # Build hidden layers
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(input_dim, hidden_dim))
            layers.append(nn.ELU())
            input_dim = hidden_dim
        
        # Output layer
        layers.append(nn.Linear(input_dim, num_actions))
        
        self.actor = nn.Sequential(*layers)
        
        # Action std (learned parameter)
        self.std = nn.Parameter(torch.zeros(num_actions))
    
    def forward(self, observations: torch.Tensor) -> torch.Tensor:
        """
        Forward pass - returns mean actions (deterministic policy for deployment).
        """
        return self.actor(observations)

def export_model(checkpoint_path: str, output_path: str = None, 
                 num_obs: int = 45, num_actions: int = 12,
                 hidden_dims: list = [512, 256, 128]):
    """
    Export actor network from checkpoint to TorchScript.
    
    Args:
        checkpoint_path: Path to the checkpoint file
        output_path: Path to save the TorchScript model
        num_obs: Number of observations
        num_actions: Number of actions
        hidden_dims: Hidden layer dimensions
    """
    if not os.path.exists(checkpoint_path):
        print(f"Error: Checkpoint file not found: {checkpoint_path}")
        sys.exit(1)
    
    # Set default output path
    if output_path is None:
        base_dir = os.path.dirname(checkpoint_path)
        output_path = os.path.join(base_dir, "policy.pt")
    
    print(f"Loading checkpoint from: {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location='cpu')
    
    # Extract state dict
    if 'model_state_dict' in checkpoint:
        state_dict = checkpoint['model_state_dict']
        print(f"Checkpoint info:")
        print(f"  - Iteration: {checkpoint.get('iter', 'N/A')}")
        if 'infos' in checkpoint:
            print(f"  - Infos: {checkpoint['infos']}")
    else:
        print("Error: 'model_state_dict' not found in checkpoint")
        sys.exit(1)
    
    # Try to infer network dimensions from state dict
    print("\nAnalyzing model architecture...")
    actor_keys = [k for k in state_dict.keys() if k.startswith('actor.')]
    
    # Find layer dimensions
    detected_dims = []
    for key in sorted(actor_keys):
        if 'weight' in key:
            shape = state_dict[key].shape
            print(f"  {key}: {shape}")
            if len(detected_dims) == 0:
                detected_dims.append(shape[1])  # Input dim
            detected_dims.append(shape[0])  # Output dim
    
    if len(detected_dims) >= 2:
        detected_num_obs = detected_dims[0]
        detected_num_actions = detected_dims[-1]
        detected_hidden_dims = detected_dims[1:-1]
        
        print(f"\nDetected architecture:")
        print(f"  - Input (observations): {detected_num_obs}")
        print(f"  - Hidden layers: {detected_hidden_dims}")
        print(f"  - Output (actions): {detected_num_actions}")
        
        # Use detected dimensions
        num_obs = detected_num_obs
        num_actions = detected_num_actions
        hidden_dims = detected_hidden_dims
    
    # Create model with detected architecture
    print(f"\nCreating model...")
    model = ActorNetwork(num_obs, num_actions, hidden_dims)
    
    # Filter state dict to only include actor and std parameters
    actor_state_dict = {k.replace('actor.', ''): v for k, v in state_dict.items() 
                       if k.startswith('actor.')}
    if 'std' in state_dict:
        actor_state_dict['std'] = state_dict['std']
    
    # Load weights
    print("Loading weights...")
    model.load_state_dict(actor_state_dict, strict=False)
    
    # Set to eval mode
    model.eval()
    
    # Test forward pass
    print("Testing forward pass...")
    dummy_input = torch.randn(1, num_obs)
    with torch.no_grad():
        output = model(dummy_input)
        print(f"  Input shape: {dummy_input.shape}")
        print(f"  Output shape: {output.shape}")
        print(f"  Output sample: {output[0, :3].tolist()}")
    
    # Convert to TorchScript using tracing
    print("\nConverting to TorchScript (using torch.jit.trace)...")
    traced_model = torch.jit.trace(model, dummy_input)
    
    # Save the model
    print(f"Saving TorchScript model to: {output_path}")
    traced_model.save(output_path)
    
    # Verify the saved model
    print("Verifying saved model...")
    loaded_model = torch.jit.load(output_path)
    with torch.no_grad():
        output2 = loaded_model(dummy_input)
        assert torch.allclose(output, output2, atol=1e-6), "Model outputs don't match!"
    
    print("\n✓ Model successfully exported and verified!")
    print(f"\nOutput file: {output_path}")
    print(f"File size: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")
    
    return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export Isaac Lab model to TorchScript")
    parser.add_argument("checkpoint", help="Path to checkpoint file (.pt)")
    parser.add_argument("-o", "--output", help="Output path for TorchScript model")
    parser.add_argument("--num-obs", type=int, default=45, help="Number of observations")
    parser.add_argument("--num-actions", type=int, default=12, help="Number of actions")
    parser.add_argument("--hidden-dims", type=int, nargs="+", default=[512, 256, 128],
                       help="Hidden layer dimensions")
    
    args = parser.parse_args()
    
    export_model(
        args.checkpoint,
        args.output,
        args.num_obs,
        args.num_actions,
        args.hidden_dims
    )
