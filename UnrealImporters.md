# Unreal Engine 4 Importing Features

Many of the features discussed here are unique to the unreal importer as they are significant changes to the data which won't necessarily be wanted unless you were importing straight into a realtime engine.

## Origin Shifting

For some reason all the maps from Red Storm Entertainment have the map static geometry well over 50,000 units away from the origin. This is problematic because the bounds of all meshes are extremely large which produces issues with visibility calculations, pivoting/scaling and just generally working with any MAP geometry is troublesome. It also means that math precision is significantly reduced due to the limits of single precision floating point numbers. Shifting all geometry closer to the origin makes for faster rendering, smoother movement, more accurate collisions, and generally a better experience.

This shifting is done in 2 stages. First, every vertex in a geometry object is considered for a bounding box. This bounding box can be used to determine an offset for this object. This offset can be subtracted from each vertex moving those vertices closer to a local origin for that object. Geometry objects in Rainbow Six and Rogue Spear maps tend to correlate with rooms, so it is easy to visualise the result. Picture rotating a room and it's contents, originally it would have been swinging around like it's on the end of a 500m (or yard) boom arm, now it will rotate around the center of the room. This new geometry object is then moved back by it's calculated offset so it appears like nothing has changed.

The second stage involves a world bounding box that is calculated by merging the bounding boxes from each geometry object. Every geometry object is then shifted back by a world offset so everything is around the global origin.

The world offset calculated in the second stage can be used for moving lights and other positions when needed.

## Geometry Merging

Rogue Spear in particular has a lot of geometry separated into separate meshes unnecessarily. While this is useful when an artist is still working on a level, it's not useful when rendering and is slower to render. When importing a set of meshes into a single object the importer can optionally merge any meshes that share the same material index. This significantly reduces the number of draw calls required to render a scene.