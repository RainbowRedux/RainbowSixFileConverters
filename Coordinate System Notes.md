The rainbow six engines use a Left handed coordinate Y-up system with the following properties

```
FORWARD_VECTOR  0.0 0.0 1.0
UP_VECTOR       0.0 1.0 0.0
RIGHT_VECTOR    1.0 0.0 0.0
```

Blender uses a Right handed coordinate Z-up system with the following properties

```
FORWARD_VECTOR  -1.0  0.0 0.0
UP_VECTOR       0.0   0.0 1.0
RIGHT_VECTOR    0.0   1.0 0.0
```

Current steps are:

1. Invert the Z axis by multiplying by -1.0
2. Rotate on the X axis by 90 degrees

To convert from RSE engines to blender perform the following steps:

1. Invert the X axis by multiplying by -1.0
2. Rotate on the Z axis by 90 degrees CW
3. Rotate on the Y axis by 90 degrees CCW

This needs to be verified once opening Rogue Spear maps in the Rommel editor and achieving the same in blender
