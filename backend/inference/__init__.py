"""
Inference module for SkinAI Chat Model
Provides disease prediction and treatment generation based on user symptoms
"""

from .inference import InferencePipeline, get_inference_pipeline

__all__ = ['InferencePipeline', 'get_inference_pipeline']
