# SPDX-FileCopyrightText: 2025-2026 The French Monkey
# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name": "Cloud",
    "author": "The French Monkey",
    "version": (1, 0, 1),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Cloud",
    "description": "Generate parametric cloud",
    "category": "Add Mesh",
    "license": "GPL-3.0-or-later",
}

import bpy
import bmesh
import math
from math import radians
from mathutils import Matrix, Vector
import mathutils.noise as noise
import random

# ------------------------------------------------------------------------
# Cloud Geometry Generators
# ------------------------------------------------------------------------

def _make_blobbed_bmesh(props):
    bm = bmesh.new(); rng = random.Random(props.seed)
    count, base, spread, elong, flatness, segs = props.blob_count, props.base_radius, props.spread, props.elongation, props.bottom_flatten, props.segments
    rings, noise_scale = max(3, segs // 2), 0.4 / spread
    a = props.elong_angle % math.tau if getattr(props, "elong_use_angle", False) else rng.uniform(0.0, math.tau)
    vx, vy, vz = Vector((math.cos(a), math.sin(a), 0.0)).normalized()
    s = 1.0 + elong
    elong_mtx = Matrix(((1 + (s - 1) * vx * vx, (s - 1) * vx * vy, (s - 1) * vx * vz),
                        ((s - 1) * vy * vx, 1 + (s - 1) * vy * vy, (s - 1) * vy * vz),
                        ((s - 1) * vz * vx, (s - 1) * vz * vy, 1 + (s - 1) * vz * vz)))
    min_dist, positions, attempts = spread * 0.15, [], count * 50
    while len(positions) < count and attempts > 0:
        attempts -= 1; direction = Vector((rng.uniform(-1,1), rng.uniform(-1,1), rng.uniform(-0.5,0.9)))
        if direction.length == 0: continue
        direction.normalize(); pos = direction * (spread * (rng.random() ** 0.5))
        if noise.noise(pos * noise_scale) < 0.2 or any((pos - p).length < min_dist for p in positions): continue
        positions.append(pos)
    while len(positions) < count:
        d = Vector((rng.uniform(-1,1), rng.uniform(-1,1), rng.uniform(-0.5,0.9)))
        if d.length == 0: continue
        d.normalize(); positions.append(d * (spread * rng.random()))
    if positions: c = sum((p for p in positions), Vector()) / len(positions); positions = [p - c for p in positions]
    for pos in positions:
        if pos.z < 0.0: pos.z *= (1.0 - flatness * min(1.0, abs(pos.z) / (spread * 0.6)))
        r = base * rng.uniform(0.7,1.3) * (1.0 - max(0.0, pos.z / (spread * 1.3)))
        T, U = Matrix.Translation(pos), Matrix.Diagonal((r, r, r, 1.0))
        E = Matrix(((elong_mtx[0][0], elong_mtx[0][1], elong_mtx[0][2], 0.0),
                    (elong_mtx[1][0], elong_mtx[1][1], elong_mtx[1][2], 0.0),
                    (elong_mtx[2][0], elong_mtx[2][1], elong_mtx[2][2], 0.0),
                    (0.0,0.0,0.0,1.0)))
        ret = bmesh.ops.create_uvsphere(bm, u_segments=max(8,segs), v_segments=max(6,rings), radius=1.0)
        bmesh.ops.transform(bm, matrix=T @ E @ U, verts=ret["verts"])
        if props.blob_displace > 0.0:
            for v in ret["verts"]: v.co += Vector(noise.noise_vector(v.co * 2.0)) * (props.blob_displace * 0.3)
    if flatness > 0.0:
        z_min = min((v.co.z for v in bm.verts), default=0.0)
        if z_min < 0.0:
            scale = 1.0 - flatness
            for v in bm.verts:
                if v.co.z < 0.0:
                    f = (v.co.z - z_min) / abs(z_min)
                    v.co.z *= (scale + (1.0 - scale) * f)
    return bm

def _make_layered_bmesh(props):
    bm = bmesh.new(); rng = random.Random(props.seed)
    count, base, spread, elong, flatness, segs = props.blob_count, props.base_radius, props.spread, props.elongation, props.bottom_flatten, props.segments
    rings, noise_scale = max(3, segs // 2), 0.3 / max(spread, 1e-6)
    thickness = base * (1.0 + elong * 0.5)
    a = props.elong_angle % math.tau if getattr(props, "elong_use_angle", False) else rng.uniform(0.0, math.tau)
    vx, vy, vz = Vector((math.cos(a), math.sin(a), 0.0)).normalized()
    s = 1.0 + elong
    elong_mtx = Matrix(((1 + (s - 1) * vx * vx, (s - 1) * vx * vy, (s - 1) * vx * vz),
                        ((s - 1) * vy * vx, 1 + (s - 1) * vy * vy, (s - 1) * vy * vz),
                        ((s - 1) * vz * vx, (s - 1) * vz * vy, 1 + (s - 1) * vz * vz)))
    for i in range(count):
        z_layer = rng.uniform(-thickness * 0.4, thickness * 0.6); z_fade = 1.0 - abs(z_layer / (thickness * 0.6))
        if rng.random() > z_fade + 0.1: continue
        pos = Vector((rng.uniform(-spread, spread), rng.uniform(-spread, spread), z_layer))
        density = (noise.noise(pos * noise_scale) + 1) / 2
        if density < 0.25: continue
        r = base * rng.uniform(0.7, 1.3) * (0.8 + density * 0.4) * (0.6 + z_fade * 0.5)
        T, U = Matrix.Translation(pos), Matrix.Diagonal((r, r, r * (0.7 + (1.0 - flatness) * 0.3), 1.0))
        E = Matrix(((elong_mtx[0][0], elong_mtx[0][1], elong_mtx[0][2], 0.0),
                    (elong_mtx[1][0], elong_mtx[1][1], elong_mtx[1][2], 0.0),
                    (elong_mtx[2][0], elong_mtx[2][1], elong_mtx[2][2], 0.0),
                    (0.0,0.0,0.0,1.0)))
        ret = bmesh.ops.create_uvsphere(bm, u_segments=max(8,segs), v_segments=max(6,rings), radius=1.0)
        bmesh.ops.transform(bm, matrix=T @ E @ U, verts=ret["verts"])
        if props.blob_displace > 0.0:
            for v in ret["verts"]: v.co += Vector(noise.noise_vector(v.co * 2.0)) * (props.blob_displace * 0.3)
    if flatness > 0.0:
        z_min = min((v.co.z for v in bm.verts), default=0.0)
        if z_min < 0.0:
            scale = 1.0 - flatness
            for v in bm.verts:
                if v.co.z < 0.0:
                    f = (v.co.z - z_min) / abs(z_min)
                    v.co.z *= (scale + (1.0 - scale) * f)
    return bm

def build_layered_cloud_mesh(name, props):
    bm = _make_layered_bmesh(props)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return mesh

def build_cloud_mesh(name, props):
    bm = _make_blobbed_bmesh(props)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh); bm.free(); mesh.update()
    return mesh

def _ensure_bottom_plane(owner_obj, spread):
    name = "CG_Floor_Plane"
    for ch in owner_obj.children:
        if ch.type == 'MESH' and ch.name == name: return ch
    mesh = bpy.data.meshes.new(name)
    plane_obj = bpy.data.objects.new(name, mesh)
    coll = owner_obj.users_collection[0] if owner_obj.users_collection else bpy.context.collection
    coll.objects.link(plane_obj)
    plane_obj.parent = owner_obj
    plane_obj.matrix_parent_inverse = owner_obj.matrix_world.inverted()
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=spread * 4.0)
    bm.to_mesh(mesh); bm.free()
    plane_obj.location = (0.0, 0.0, 0.0)
    plane_obj.hide_set(True); plane_obj.hide_render = True
    return plane_obj

def _paint_bottom_mask(obj, group_name, spread, intensity):
    vg = obj.vertex_groups.get(group_name) or obj.vertex_groups.new(name=group_name)
    vg.remove([v.index for v in obj.data.vertices])
    limit = max(0.001, spread * 0.6); weights = []
    for v in obj.data.vertices:
        z = v.co.z
        w = min(1.0, (-z) / limit) * intensity if z < 0.0 else 0.0
        weights.append(w)
    vg.add([v.index for v, w in zip(obj.data.vertices, weights) if w > 0.0], 1.0, 'REPLACE')
    for i, w in enumerate(weights):
        if w > 0.0: vg.add([i], w, 'REPLACE')
    return vg

# ------------------------------------------------------------------------
# Rebuild / Generate
# ------------------------------------------------------------------------

def _apply_all_modifiers(obj, mod_names):
    view_layer = bpy.context.view_layer
    view_layer.objects.active = obj; obj.select_set(True)
    for mn in mod_names:
        try: bpy.ops.object.modifier_apply(modifier=mn)
        except Exception: pass

def _remesh_and_smooth(o, props):
    for mn in ("CG_VoxelRemesh", "CG_Smooth", "CG_Displace", "CG_Flatten"):
        if mn in o.modifiers:
            o.modifiers.remove(o.modifiers[mn])

    bpy.context.view_layer.objects.active = o
    o.select_set(True)

    rem = o.modifiers.new("CG_VoxelRemesh", "REMESH")
    rem.mode = 'VOXEL'
    rem.voxel_size = props.voxel_size
    rem.adaptivity = 0.0
    rem.use_smooth_shade = True

    sm = o.modifiers.new("CG_Smooth", "SMOOTH")
    sm.factor = props.smooth_factor
    sm.iterations = props.smooth_iterations

    tex_name = "CloudNoiseTex"
    tex = bpy.data.textures.get(tex_name) or bpy.data.textures.new(tex_name, type='CLOUDS')
    tex.noise_scale = props.noise_scale
    tex.noise_depth = 2

    disp = o.modifiers.new("CG_Displace", "DISPLACE")
    disp.texture = tex
    disp.texture_coords = 'GLOBAL'
    disp.strength = max(0.2, props.voxel_size * 50.0 * props.noise_scale)

    if props.bottom_flatten > 0.0 and getattr(props, "cloud_type", "BLOBBED") == "BLOBBED":
        plane = _ensure_bottom_plane(o, props.spread)
        _paint_bottom_mask(o, "CG_BottomMask", props.spread, props.bottom_flatten)
        flat = o.modifiers.new("CG_Flatten", "SHRINKWRAP")
        flat.target = plane
        flat.wrap_method = 'PROJECT'
        flat.use_project_z = True
        flat.use_negative_direction = True
        flat.use_positive_direction = False
        flat.project_limit = props.spread * 3.0
        flat.vertex_group = "CG_BottomMask"
        flat.offset = 0.0

    try:
        bpy.ops.object.shade_smooth()
    except Exception:
        pass

def rebuild_cloud(obj):
    if not obj or obj.type != "MESH":
        return False

    class _P: pass
    p = _P()
    keys = ("seed","blob_count","base_radius","spread","elongation","elong_use_angle",
            "elong_angle","bottom_flatten","segments","voxel_size","smooth_iterations","blob_displace",
            "smooth_factor","noise_scale")
    for k in keys:
        if k in obj:
            setattr(p, k, obj[k])

    new_mesh = build_cloud_mesh("CloudRawMesh", p)
    old_mesh = obj.data

    obj.data = new_mesh
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    if old_mesh and old_mesh.users == 0:
        bpy.data.meshes.remove(old_mesh)

    _remesh_and_smooth(obj, p)
    return True

def rebuild_layered_cloud(obj):
    if not obj or obj.type != "MESH": return False
    class _P: pass
    p = _P()
    keys = ("seed","blob_count","base_radius","spread","elongation","elong_use_angle",
            "elong_angle","bottom_flatten","segments","voxel_size","smooth_iterations",
            "smooth_factor","noise_scale","blob_displace")
    for k in keys:
        if k in obj: setattr(p, k, obj[k])
    setattr(p, "cloud_type", obj.get("cloud_type", "LAYERED"))
    new_mesh = build_layered_cloud_mesh("CloudRawMesh", p)
    old_mesh = obj.data
    obj.data = new_mesh
    bpy.context.view_layer.objects.active = obj; obj.select_set(True)
    if old_mesh and old_mesh.users == 0: bpy.data.meshes.remove(old_mesh)
    _remesh_and_smooth(obj, p)
    return True

def generate_cloud(context):
    p, obj = context.scene.cgen_props, context.active_object

    if p.cloud_type == 'BLOBBED':
        mesh_func = build_cloud_mesh
    else:
        mesh_func = build_layered_cloud_mesh 

    keys = ("seed","blob_count","base_radius","spread","elongation","elong_use_angle",
            "elong_angle","bottom_flatten","segments","voxel_size","smooth_iterations","blob_displace",
            "smooth_factor")

    if obj and obj.type == "MESH" and "cloud_generator" in obj and obj.select_get():
        for k in keys: obj[k] = getattr(p, k)
        new_mesh = mesh_func("CloudRawMesh", p)
        old_mesh = obj.data
        obj.data = new_mesh
        if old_mesh and old_mesh.users == 0: bpy.data.meshes.remove(old_mesh)
        _remesh_and_smooth(obj, p)
        obj.name = obj.data.name = "Cloud"
        return obj

    mesh = bpy.data.meshes.new("CloudRawMesh")
    new_obj = bpy.data.objects.new("Cloud", mesh)
    context.collection.objects.link(new_obj)
    context.view_layer.objects.active = new_obj; new_obj.select_set(True)
    for k in keys: new_obj[k] = getattr(p, k)
    new_obj["cloud_generator"] = True
    new_mesh = mesh_func("CloudRawMesh", p)
    new_obj.data = new_mesh
    _remesh_and_smooth(new_obj, p)
    return new_obj

# ------------------------------------------------------------------------
# Live Update
# ------------------------------------------------------------------------

def update_cloud(self, context):
    p = context.scene.cgen_props
    if not p.live_update:
        return

    o = context.active_object
    if not (o and o.type == "MESH" and "cloud_generator" in o and o.select_get()):
        return

    for k in (
        "seed", "blob_count", "base_radius", "spread", "elongation", "elong_use_angle",
        "elong_angle", "bottom_flatten", "segments", "voxel_size", "smooth_iterations",
        "smooth_factor", "blob_displace", "noise_scale"
    ):
        o[k] = getattr(p, k)

    if not o.data:
        return

    if p.cloud_type == 'BLOBBED':
        rebuild_cloud(o)
    else:
        rebuild_layered_cloud(o)

# ------------------------------------------------------------------------
# UI Properties
# ------------------------------------------------------------------------

class CGProperties(bpy.types.PropertyGroup):
    live_update: bpy.props.BoolProperty(
        name="Live Update",
        default=False,
        description="Update cloud in real-time as parameters change"
    )
    cloud_type: bpy.props.EnumProperty(
    name="Cloud Type",
    description="Select which type of cloud generation to use",
    items=[
        ('BLOBBED', "Blobbed", "Puffy, spherical blob clouds"),
        ('LAYERED', "Layered", "Flat, stretched cloud layer"),
    ],
    default='BLOBBED',
    update=update_cloud
    )

    seed: bpy.props.IntProperty(name="Seed", default=1, min=0, max=999999, description="Random seed for blob placement", update=update_cloud)
    blob_count: bpy.props.IntProperty(name="Blobs", default=28, min=1, max=50, description="Number of spheres composing the cloud", update=update_cloud)
    base_radius: bpy.props.FloatProperty(name="Blob Radius", default=0.6, min=0.05, max=50.0, subtype='DISTANCE', description="Average radius of each blob before merging", update=update_cloud)
    spread: bpy.props.FloatProperty(name="Spread", default=2.0, min=0.1, max=100.0, subtype='DISTANCE', description="Overall size (radius) of the cloud cluster", update=update_cloud)
    elongation: bpy.props.FloatProperty(name="Elongation", default=0.25, min=0.0, max=10.0, description="Stretch the cloud along a horizontal axis for natural shapes", update=update_cloud)
    segments: bpy.props.IntProperty(name="Blob Segments", default=16, min=8, max=32, description="Base sphere segment count (higher = smoother, slower)", update=update_cloud)

    voxel_size: bpy.props.FloatProperty(name="Voxel Size", default=0.08, min=0.005, max=1.0, subtype='DISTANCE', description="Smaller voxels create finer, puffier detail (slower)", update=update_cloud)
    smooth_iterations: bpy.props.IntProperty(name="Smooth Iterations", default=12, min=0, max=100, description="Number of smoothing passes after remesh", update=update_cloud)
    smooth_factor: bpy.props.FloatProperty(name="Smooth Factor", default=0.7, min=0.0, max=1.0, description="Strength of each smoothing pass", update=update_cloud)
    bottom_flatten: bpy.props.FloatProperty(name="Bottom Flatten", default=0.5, min=0.0, max=1.0, description="Flatten the bottom portion of the cloud (0=none, 1=completely flat)", update=update_cloud)

    elong_use_angle: bpy.props.BoolProperty(name="Use Elongation Angle", default=False, description="Use a fixed horizontal angle for elongation instead of a random direction", update=update_cloud)
    elong_angle: bpy.props.FloatProperty(name="Elongation Angle", default=0.0, subtype='ANGLE', min=0.0, max=math.tau, description="Elongation direction in the XY plane (0° = +X, 90° = +Y)", update=update_cloud)
    noise_scale: bpy.props.FloatProperty(name="Noise Scale", default=0.5, min=0.05, max=5.0, description="Controls the scale of the displacement noise pattern", update=update_cloud)
    blob_displace: bpy.props.FloatProperty(name="Blob Displace", default=0.3, min=0.0, max=200.0, description="Adds random displacement to each blob to break up the spherical look", update=update_cloud)

# ------------------------------------------------------------------------
# Operators
# ------------------------------------------------------------------------

class CG_OT_generate(bpy.types.Operator):
    bl_idname = "cg.generate"
    bl_label = "Generate Cloud"
    bl_description = "Generate/remesh a puffy cloud mesh"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        generate_cloud(context)
        return {"FINISHED"}
    
class CG_OT_delete_cloud(bpy.types.Operator):
    bl_idname = "cg.delete_cloud"
    bl_label = "Delete Cloud"
    bl_description = "Delete the selected cloud and all of its children"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH' or "cloud_generator" not in obj:
            self.report({'WARNING'}, "No cloud object selected")
            return {'CANCELLED'}

        to_delete = [obj] + list(obj.children)

        for o in to_delete:
            for coll in o.users_collection:
                coll.objects.unlink(o)
            bpy.data.objects.remove(o, do_unlink=True)

        self.report({'INFO'}, f"Deleted {len(to_delete)} object(s)")
        return {'FINISHED'}

# ------------------------------------------------------------------------
# UI
# ------------------------------------------------------------------------

class VIEW3D_PT_cloud_generator(bpy.types.Panel):
    bl_label = "Cloud"
    bl_idname = "VIEW3D_PT_cloud_generator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cloud"

    def draw(self, context):
        layout = self.layout
        p = context.scene.cgen_props
        o = context.object

        row = layout.row(align=True)
        row.operator("cg.generate", icon="OUTLINER_DATA_VOLUME")

        row = layout.row(align=True)
        row.prop(p, "live_update", toggle=True)

        layout.separator(factor=0.5)

        layout.prop(p, "cloud_type", expand=True)

        col = layout.column(align=True)
        col.prop(p, "seed", slider=True)
        col.prop(p, "blob_count", slider=True)
        col.prop(p, "base_radius", slider=True)
        col.prop(p, "spread", slider=True)
        col.prop(p, "elongation", slider=True)
        col.prop(p, "blob_displace", slider=True)

        col.separator(factor=0.5)

        col.prop(p, "bottom_flatten", slider=True)
        col.prop(p, "segments", slider=True)
        col.prop(p, "noise_scale", slider=True)

        col.separator(factor=0.5)

        col.prop(p, "voxel_size", slider=True)
        col.prop(p, "smooth_iterations", slider=True)
        col.prop(p, "smooth_factor", slider=True)

        layout.separator(factor=0.5)

        row = layout.row(align=True)
        row.prop(p, "elong_use_angle", toggle=True, icon="ORIENTATION_GIMBAL")

        if p.elong_use_angle:
            layout.prop(p, "elong_angle", slider=True)

        layout.separator(factor=0.5)

        if o and o.type == "MESH" and "cloud_generator" in o and o.select_get():
            row = layout.row(align=True)
            row.operator("cg.delete_cloud", icon="TRASH", text="Delete Cloud")
            layout.label(text=f"Editing: {o.name}", icon="OUTLINER_DATA_VOLUME")
        else:
            layout.label(text="No cloud object selected", icon="INFO")

# ------------------------------------------------------------------------
# Registration
# ------------------------------------------------------------------------

classes = (
    CGProperties,
    CG_OT_generate,
    CG_OT_delete_cloud, 
    VIEW3D_PT_cloud_generator, 
)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.cgen_props = bpy.props.PointerProperty(type=CGProperties)

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.cgen_props

if __name__ == "__main__":
    register()
