"""This module should import and initialize all modules required by unreal"""

from PIL import Image

import unreal_engine
from unreal_engine.classes import Blueprint

actorFullClass = "/Game/Rainbow/TestActor.TestActor"
loadedActorClass = None
loadedActorClass = unreal_engine.load_object(Blueprint, actorFullClass)

from unreal_engine.classes import TestActor
from UnrealImporters.ImportSOB import RSEResourceLoader
from UnrealImporters import ImportSOB
