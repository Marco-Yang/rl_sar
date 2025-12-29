#!/usr/bin/env python3
"""
Convert Isaac Lab trained model checkpoint to TorchScript format for C++ inference.

This script loads a PyTorch model checkpoint (.pt) and exports it as TorchScript,
which can be loaded by LibTorch in C++ applications.
"""

import torch
import argparse
import os
import sys

def convert_model_to_torchscript(input_path: str, output_path: str = None):
    """
    Convert a PyTorch model checkpoint to TorchScript format.
    
    Args:
        input_path: Path to the input .pt model checkpoint
        output_path: Path to save the TorchScript model (optional)
    """
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    # Set default output path if not provided
    if output_path is None:
        base_dir = os.path.dirname(input_path)
        output_path = os.path.join(base_dir, "policy.pt")
    
    print(f"Loading model from: {input_path}")
    
    try:
        # Load the checkpoint
        checkpoint = torch.load(input_path, map_location='cpu')
        
        # Try to extract the model from checkpoint
        if isinstance(checkpoint, dict):
            # Check common checkpoint keys
            if 'model_state_dict' in checkpoint:
                model_state = checkpoint['model_state_dict']
                print("Found 'model_state_dict' in checkpoint")
            elif 'actor_critic' in checkpoint:
                model_state = checkpoint['actor_critic']
                print("Found 'actor_critic' in checkpoint")
            elif 'policy' in checkpoint:
                model_state = checkpoint['policy']
                print("Found 'policy' in checkpoint")
            else:
                print("Checkpoint keys:", list(checkpoint.keys()))
                print("\nError: Cannot find model in checkpoint.")
                print("Please check the checkpoint structure and modify this script accordingly.")
                sys.exit(1)
        else:
            # Checkpoint might be the model directly
            model_state = checkpoint
            print("Checkpoint appears to be the model directly")
        
        # If model_state is a state_dict, we need to reconstruct the model
        # This is tricky without knowing the exact model architecture
        if isinstance(model_state, dict) and not hasattr(model_state, 'forward'):
            print("\nError: The checkpoint contains only state_dict, not the full model.")
            print("We need the model architecture to convert it to TorchScript.")
            print("\nOptions:")
            print("1. Export the model from Isaac Lab using torch.jit.script() or torch.jit.trace()")
            print("2. Provide the model architecture code to reconstruct it")
            print("\nTo export from Isaac Lab, add this to your training script:")
            print("  scripted_model = torch.jit.script(model)")
            print("  scripted_model.save('policy.pt')")
            sys.exit(1)
        
        # Try to script the model
        print("Converting to TorchScript...")
        scripted_model = torch.jit.script(model_state)
        
        # Save the scripted model
        print(f"Saving TorchScript model to: {output_path}")
        scripted_model.save(output_path)
        
        # Verify the saved model
        print("Verifying saved model...")
        loaded_model = torch.jit.load(output_path)
        print("✓ Model successfully converted and verified!")
        
        # Print model info
        print(f"\nModel saved to: {output_path}")
        print(f"File size: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")
        
    except Exception as e:
        print(f"\nError during conversion: {e}")
        print("\nThe model checkpoint format is not directly convertible.")
        print("You need to export the model from Isaac Lab during training.")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert PyTorch model to TorchScript")
    parser.add_argument("input", help="Input model checkpoint path (.pt file)")
    parser.add_argument("-o", "--output", help="Output TorchScript model path (default: policy.pt in same directory)")
    
    args = parser.parse_args()
    
    convert_model_to_torchscript(args.input, args.output)
