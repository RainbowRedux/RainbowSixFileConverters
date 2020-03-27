"""
Constants used throughout the code base
"""

class RSEGameVersions(object):
    """Used to group some related constants, somewhat like an enum
    Stores constants specifiying game versions"""
    RAINBOW_SIX = "R6"
    ROGUE_SPEAR = "RS"
    UNKNOWN = "??"

class RSEEngineVersions(object):
    """Used to store constants representing the different engine versions available"""
    UNKNOWN = "Unknown"
    SHERMAN = "Sherman" # Rainbow Six, Eagle Watch
    ROMMEL = "Rommel" # Rogue Spear, Urban Ops, Covert Ops, Black Ops
    IKE = "Ike" # Ghost Recon

class RSEMaterialFormatConstants(object):
    """Used to group some related constants, somewhat like an enum
    Stores sizes of materials in each game version"""
    RSE_MATERIAL_SIZE_NO_STRINGS_ROGUE_SPEAR = 69 #Usually accurate if you only remove texturename string length
    RSE_MATERIAL_SIZE_NO_STRINGS_RAINBOW_SIX = 73

class RSELightTypes(object):
    """Stores the light type as used in light objects"""
    SPOTLIGHT = 1
    POINTLIGHT = -1
    UNKNOWN = -1

#decided to not use Enum for python2.7 compatibility
class RSEAlphaMethod(object):
    """Stores the different alpha methods available for materials"""
    SAM_Opaque       = 1
    SAM_Unknown      = 2
    SAM_MethodLookup = 3 # This means exact method is defined in the Sherman.CXP or Rommel.CXP files

#Rommel editor defines the flags
#Not Collidable2d
#Not Collidable3d
#Not Rendered
#climbable
#FloorPolygon
#45+ Floor Polygon
#NotShownInPlan
class RSEGeometryFlags(object):
    """Provides constants to identify each flag in a GeometryFlag variable,
    as well as helper methods to expand all flags into human readable form"""
    #Each of these flags masks an individual bit in a DWORD (32bit number)
    FLAG_CONSTANTS = {
        "GF_CLIMBABLE" :    0x00000001, # Object can be climbed like a ladder
        "GF_NOCOLLIDE2D" :     0x00000002, # No 2D collision
        "GF_INVISIBLE" :    0x00000004, # invisible, for RS collision geometry also appears to be "ignored for all collision"
        "GF_UNKNOWN2" :     0x00000008, # ?? Probably Floor45+
        "GF_FLOORPOLYGON" :    0x00000010, # This is a floor surface
        "GF_NOCOLLIDE3D" :    0x00000020, # Can be shot through / seen through
        "GF_UNKNOWN4" :     0x00000040, # ?? not seen yet
        "GF_NOTSHOWNINPLAN" :     0x00000080, # Not rendered in 2D Map views
    }

    @staticmethod
    def EvaluateFlags(flags):
        """Expands flags stored in a uint into a human readable dictionary"""
        results = {}
        sumFlags = 0
        for flagName, flagMaskVal in RSEGeometryFlags.FLAG_CONSTANTS.items():
            sumFlags += flagMaskVal
            if flagMaskVal & flags > 0:
                results[flagName] = True
            else:
                results[flagName] = False

        if flags > sumFlags:
            results["UnevaluatedFlags"] =  True
        else:
            results["UnevaluatedFlags"] =  False

        return results


UINT_MAX = 4294967295
