"""Independent REST adapters; all I/O is supplied through a transport."""
from .minimax import MiniMaxAdapter
from .fish import FishAdapter
from .elevenlabs import ElevenLabsAdapter
from .azure import AzureAdapter

ADAPTERS = {adapter.name: adapter() for adapter in (
    MiniMaxAdapter, FishAdapter, ElevenLabsAdapter, AzureAdapter)}
