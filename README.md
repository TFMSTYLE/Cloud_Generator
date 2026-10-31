# Cloud Generator

![cloud-thumb](https://github.com/user-attachments/assets/f1660c58-e10e-4344-b298-bc83b8c9d0cb)

**Author:** The French Monkey (TFMSTYLE)  
**Version:** 1.0.3  

---

## Overview

The Cloud Generator creates parametric volumetric-like cloud meshes by merging multiple procedural spheres with customizable shapes and noise deformation.  
It supports two generation modes—**Blobbed** and **Layered**—to simulate puffy cumulus formations or flat stratus-style cloud layers.  
Each cloud mesh can be remeshed, smoothed, and displaced to achieve organic and natural results suitable for both stylized and realistic rendering.

---

## Parameters

### Live Update
When enabled, the cloud automatically regenerates whenever a parameter changes.  
Useful for fast visual feedback, but may slow performance with high-resolution settings.

---

### Cloud Type
Selects the overall style of cloud generation.

- **Blobbed** – Puffy, spherical cluster resembling cumulus clouds.  
- **Layered** – Flatter, spread-out formation ideal for atmospheric layers.

---

### Seed
Sets the random seed used for blob placement and shape variation.  
Changing the seed generates a new formation with the same parameters.

---

### Blobs
Number of spheres composing the cloud.  
Higher values produce more detailed and complex shapes.

---

### Blob Radius
Base radius of each individual blob before merging.  
Controls the apparent “chunkiness” of the cloud.  
The slider stops at 10. Type a value to go up to 50, which takes longer to generate.

---

### Spread
Defines the overall size or radius of the cloud cluster.  
Larger spreads result in wider, more diffuse formations.

---

### Elongation
Stretches the cloud along a random or user-defined horizontal direction.  
Higher values create elongated, wind-swept shapes.

---

### Blob Segments
Number of subdivisions per base sphere.  
Increasing this produces smoother geometry but increases computation time.

---

### Voxel Size
Sets the voxel remesh resolution.  
Smaller values yield finer, more detailed puffs at the cost of performance.

---

### Smooth Iterations
Controls how many times the mesh is smoothed after remeshing.  
Higher values soften sharp transitions between merged blobs.

---

### Smooth Factor
Adjusts the strength of each smoothing pass.  
A balance between soft edges and retained detail.

---

### Bottom Flatten
Flattens the lower portion of the cloud mesh to simulate the base of cumulus clouds.  
A value of 1.0 makes the underside completely flat.

---

### Use Elongation Angle
When enabled, uses a fixed elongation direction instead of a random one.  
Useful for aligning multiple clouds with consistent wind direction.

---

### Elongation Angle
Specifies the angle (in degrees or radians) of the elongation axis in the XY plane.  
0° corresponds to the +X direction, and 90° to the +Y direction.

---

### Noise Scale
Controls the scale of procedural noise used in the displacement modifier.  
Larger values create broader, softer shapes; smaller values add finer detail.

---

### Blob Displace
Adds random displacement to each blob’s surface before merging.  
Breaks up the uniform spherical look to create more natural cloud variation.  
The slider stops at 20. Type a value to go up to 200, which takes longer to generate.

---

## Operators

### Generate Cloud
Creates or regenerates a cloud mesh using the current parameters.  
If a previously generated cloud is selected, it will be replaced.

---

### Delete Cloud
Removes the selected cloud object and any associated children or helper objects.

---

## Usage Notes

- Use **Blobbed** mode for volumetric cumulus formations, **Layered** for flatter atmospheric coverage.  
- Lower **Voxel Size** and higher **Smooth Iterations** yield softer, more natural results.  
- Adjust **Bottom Flatten** to control the realism of the underside shape.  
- Enable **Live Update** to preview parameter effects interactively, then disable it for performance.  
- Clouds can be shaded using volumetric or subsurface materials for realistic lighting.

---

## Install

Needs Blender 4.2 or later. Get the zip from [tfmstyle.com](https://tfmstyle.com), then in Blender open Edit > Preferences > Get Extensions, open the menu at the top right and pick Install from Disk.

To build the zip yourself, run this in the repo folder:

```bash
blender --command extension build
```

The addon is `__init__.py`, plus `relay_updater.py` for its update checks. It depends on nothing but Blender.

---

## License

GPL 3.0 or later. See [LICENSE](LICENSE).
