"""Procedurally generate a solar roof Blender scene with animation and render settings."""

import math
import os
from typing import Any

import bpy

# --- Scene configuration ---
ROOF_LENGTH = 9.66
ROOF_WIDTH = 6.23
ROOF_THICKNESS = 0.3

PANEL_WIDTH = 1.70
PANEL_LENGTH = 1.00
PANEL_THICKNESS = 0.04
PANEL_TILT_DEG = 15

PANEL_COLS = 5
PANEL_ROWS = 3
PANEL_COL_GAP = 0.03
PANEL_ROW_PITCH = 1.6

FRAME_START = 1
FRAME_END = 360
FPS = 30

RENDER_SAMPLES = 256
RENDER_NOISE_THRESHOLD = 0.05
VIEWPORT_SAMPLES = 128


def setup_scene() -> None:
    """Remove existing objects and materials to start from a clean scene."""
    for obj in list(bpy.data.objects):
        try:
            bpy.data.objects.remove(obj, do_unlink=True)
        except Exception as exc:
            print(f"Failed to remove object {obj.name}: {exc}")

    for material in list(bpy.data.materials):
        try:
            bpy.data.materials.remove(material, do_unlink=True)
        except Exception as exc:
            print(f"Failed to remove material {material.name}: {exc}")


def setup_world_lighting() -> None:
    """Configure a subtle sky background for ambient lighting and reflections."""
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world

    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()

    output = nodes.new(type="ShaderNodeOutputWorld")
    background = nodes.new(type="ShaderNodeBackground")
    sky = nodes.new(type="ShaderNodeTexSky")

    try:
        sky.sky_type = "SINGLE_SCATTERING"
    except TypeError:
        sky.sky_type = "NISHITA"
    sky.sun_elevation = math.radians(35)
    sky.sun_rotation = math.radians(180)
    background.inputs["Strength"].default_value = 0.35
    background.inputs["Color"].default_value = (0.82, 0.88, 0.95, 1.0)

    links.new(sky.outputs["Color"], background.inputs["Color"])
    links.new(background.outputs["Background"], output.inputs["Surface"])


def create_materials() -> dict[str, bpy.types.Material]:
    """Create procedural PBR materials for roof, frame, rack, and silicon cells."""
    materials: dict[str, bpy.types.Material] = {}

    mat_roof = bpy.data.materials.new(name="Concrete_Roof")
    mat_roof.use_nodes = True
    principled = mat_roof.node_tree.nodes.get("Principled BSDF")
    if principled:
        principled.inputs["Base Color"].default_value = (0.3, 0.3, 0.32, 1.0)
        principled.inputs["Roughness"].default_value = 0.8
        principled.inputs["Metallic"].default_value = 0.0
    materials["roof"] = mat_roof

    mat_frame = bpy.data.materials.new(name="Aluminium_Frame")
    mat_frame.use_nodes = True
    principled = mat_frame.node_tree.nodes.get("Principled BSDF")
    if principled:
        principled.inputs["Base Color"].default_value = (0.7, 0.7, 0.72, 1.0)
        principled.inputs["Metallic"].default_value = 0.95
        principled.inputs["Roughness"].default_value = 0.25
    materials["frame"] = mat_frame

    mat_rack = bpy.data.materials.new(name="Galvanized_Rack")
    mat_rack.use_nodes = True
    principled = mat_rack.node_tree.nodes.get("Principled BSDF")
    if principled:
        principled.inputs["Base Color"].default_value = (0.5, 0.52, 0.53, 1.0)
        principled.inputs["Metallic"].default_value = 0.8
        principled.inputs["Roughness"].default_value = 0.4
    materials["rack"] = mat_rack

    mat_silicon = bpy.data.materials.new(name="Silicon_Cells")
    mat_silicon.use_nodes = True
    nodes = mat_silicon.node_tree.nodes
    links = mat_silicon.node_tree.links
    nodes.clear()

    node_output = nodes.new(type="ShaderNodeOutputMaterial")
    node_principled = nodes.new(type="ShaderNodeBsdfPrincipled")
    node_tex_coord = nodes.new(type="ShaderNodeTexCoord")
    node_mapping = nodes.new(type="ShaderNodeMapping")
    node_brick = nodes.new(type="ShaderNodeTexBrick")

    node_brick.offset = 0.0
    node_brick.offset_frequency = 1
    node_brick.inputs["Scale"].default_value = 15.0
    node_brick.inputs["Mortar Size"].default_value = 0.015
    node_brick.inputs["Mortar Smooth"].default_value = 0.0
    node_brick.inputs["Row Height"].default_value = 1.0
    node_brick.inputs["Brick Width"].default_value = 1.0
    node_brick.inputs["Color1"].default_value = (0.02, 0.04, 0.1, 1.0)
    node_brick.inputs["Color2"].default_value = (0.02, 0.04, 0.1, 1.0)
    node_brick.inputs["Mortar"].default_value = (0.6, 0.6, 0.65, 1.0)

    links.new(node_tex_coord.outputs["Generated"], node_mapping.inputs["Vector"])
    links.new(node_mapping.outputs["Vector"], node_brick.inputs["Vector"])
    links.new(node_brick.outputs["Color"], node_principled.inputs["Base Color"])

    node_principled.inputs["Roughness"].default_value = 0.08
    node_principled.inputs["Metallic"].default_value = 0.1
    if "Specular" in node_principled.inputs:
        node_principled.inputs["Specular"].default_value = 0.9
    elif "Specular IOR Level" in node_principled.inputs:
        node_principled.inputs["Specular IOR Level"].default_value = 0.9

    links.new(node_principled.outputs["BSDF"], node_output.inputs["Surface"])
    materials["silicon"] = mat_silicon

    return materials


def build_roof(
    materials: dict[str, bpy.types.Material],
    length: float = ROOF_LENGTH,
    width: float = ROOF_WIDTH,
    thickness: float = ROOF_THICKNESS,
) -> bpy.types.Object:
    """Create the concrete roof slab."""
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -thickness / 2))
    roof_obj = bpy.context.active_object
    roof_obj.name = "Concrete_Roof_Slab"
    roof_obj.dimensions = (length, width, thickness)
    bpy.ops.object.transform_apply(scale=True)

    if roof_obj.data.materials:
        roof_obj.data.materials[0] = materials["roof"]
    else:
        roof_obj.data.materials.append(materials["roof"])

    return roof_obj


def build_single_solar_panel_assembly(
    materials: dict[str, bpy.types.Material],
    width: float = PANEL_WIDTH,
    length: float = PANEL_LENGTH,
    thickness: float = PANEL_THICKNESS,
    tilt_angle_deg: float = PANEL_TILT_DEG,
) -> bpy.types.Object:
    """Build one solar panel assembly with frame, silicon face, and support rack."""
    parts_to_join: list[bpy.types.Object] = []

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
    frame_obj = bpy.context.active_object
    frame_obj.name = "Panel_Frame"
    frame_obj.dimensions = (width, length, thickness)
    bpy.ops.object.transform_apply(scale=True)
    frame_obj.data.materials.append(materials["frame"])
    parts_to_join.append(frame_obj)

    silicon_w = width - 0.04
    silicon_l = length - 0.04
    silicon_t = 0.01
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0, 0, (thickness / 2) - (silicon_t / 2) + 0.002),
    )
    silicon_obj = bpy.context.active_object
    silicon_obj.name = "Panel_Silicon"
    silicon_obj.dimensions = (silicon_w, silicon_l, silicon_t)
    bpy.ops.object.transform_apply(scale=True)
    silicon_obj.data.materials.append(materials["silicon"])
    parts_to_join.append(silicon_obj)

    angle_rad = math.radians(tilt_angle_deg)
    clearance = 0.15

    leg_x_offsets = [-width / 2 + 0.15, width / 2 - 0.15]
    back_y = length / 2 - 0.05
    front_y = -length / 2 + 0.05
    z_offset_local = -thickness / 2

    back_y_world = back_y * math.cos(angle_rad) - z_offset_local * math.sin(angle_rad)
    back_z_world = back_y * math.sin(angle_rad) + z_offset_local * math.cos(angle_rad) + clearance

    front_y_world = front_y * math.cos(angle_rad) - z_offset_local * math.sin(angle_rad)
    front_z_world = front_y * math.sin(angle_rad) + z_offset_local * math.cos(angle_rad) + clearance

    for x in leg_x_offsets:
        leg_h = back_z_world
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x, back_y_world, leg_h / 2 - (thickness / 2)),
        )
        leg = bpy.context.active_object
        leg.name = "Rack_Leg_Back"
        leg.dimensions = (0.04, 0.04, leg_h)
        bpy.ops.object.transform_apply(scale=True)
        leg.data.materials.append(materials["rack"])
        parts_to_join.append(leg)

    for x in leg_x_offsets:
        leg_h = front_z_world
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x, front_y_world, leg_h / 2 - (thickness / 2)),
        )
        leg = bpy.context.active_object
        leg.name = "Rack_Leg_Front"
        leg.dimensions = (0.04, 0.04, leg_h)
        bpy.ops.object.transform_apply(scale=True)
        leg.data.materials.append(materials["rack"])
        parts_to_join.append(leg)

    for x in leg_x_offsets:
        dy = back_y_world - front_y_world
        dz = back_z_world - front_z_world
        beam_len = math.sqrt(dy**2 + dz**2)
        beam_angle = math.atan2(dz, dy)

        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(
                x,
                (back_y_world + front_y_world) / 2,
                (back_z_world + front_z_world) / 2 - (thickness / 2),
            ),
        )
        beam = bpy.context.active_object
        beam.name = "Rack_Beam_Diagonal"
        beam.dimensions = (0.03, beam_len, 0.03)
        beam.rotation_euler[0] = beam_angle
        bpy.ops.object.transform_apply(scale=True, rotation=True)
        beam.data.materials.append(materials["rack"])
        parts_to_join.append(beam)

    frame_obj.rotation_euler[0] = angle_rad
    frame_obj.location = (0, 0, clearance)
    bpy.ops.object.select_all(action="DESELECT")
    frame_obj.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    silicon_obj.rotation_euler[0] = angle_rad
    offset_z = (thickness / 2) - (silicon_t / 2) + 0.002
    silicon_y_world = -offset_z * math.sin(angle_rad)
    silicon_z_world = offset_z * math.cos(angle_rad) + clearance
    silicon_obj.location = (0, silicon_y_world, silicon_z_world)
    bpy.ops.object.select_all(action="DESELECT")
    silicon_obj.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    bpy.ops.object.select_all(action="DESELECT")
    for part in parts_to_join:
        part.select_set(True)

    bpy.context.view_layer.objects.active = frame_obj
    bpy.ops.object.join()

    panel_assembly = bpy.context.active_object
    panel_assembly.name = "Solar_Panel_Assembly"
    return panel_assembly


def place_solar_panels(
    panel_template: bpy.types.Object,
    panel_width: float = PANEL_WIDTH,
    panel_length: float = PANEL_LENGTH,
    num_cols: int = PANEL_COLS,
    num_rows: int = PANEL_ROWS,
    col_gap: float = PANEL_COL_GAP,
    row_pitch: float = PANEL_ROW_PITCH,
) -> list[bpy.types.Object]:
    """Place a grid of solar panel assemblies on the roof."""
    row_width_total = num_cols * panel_width + (num_cols - 1) * col_gap
    start_x = -row_width_total / 2 + panel_width / 2
    row_layout_depth = (num_rows - 1) * row_pitch
    start_y = -row_layout_depth / 2

    panels_group = bpy.data.collections.new("Solar_Panels")
    bpy.context.scene.collection.children.link(panels_group)

    panel_objects: list[bpy.types.Object] = []
    first_panel = True

    for row in range(num_rows):
        y_pos = start_y + row * row_pitch
        for col in range(num_cols):
            x_pos = start_x + col * (panel_width + col_gap)

            if first_panel:
                panel_template.location = (x_pos, y_pos, 0)
                try:
                    bpy.context.scene.collection.objects.unlink(panel_template)
                except RuntimeError:
                    pass
                panels_group.objects.link(panel_template)
                panel_objects.append(panel_template)
                first_panel = False
            else:
                new_panel = panel_template.copy()
                new_panel.data = panel_template.data
                new_panel.location = (x_pos, y_pos, 0)
                panels_group.objects.link(new_panel)
                panel_objects.append(new_panel)

    return panel_objects


def add_lighting_and_camera() -> tuple[bpy.types.Object, bpy.types.Object]:
    """Add sun light, camera with track constraint, and set the active scene camera."""
    bpy.ops.object.light_add(type="SUN", radius=1, align="WORLD", location=(5, -5, 10))
    sun = bpy.context.active_object
    sun.name = "Sun_Light"
    sun.data.energy = 4.0
    sun.rotation_euler = (math.radians(45), 0, math.radians(30))

    bpy.ops.object.camera_add(align="WORLD", location=(10, -12, 8))
    camera = bpy.context.active_object
    camera.name = "View_Camera"
    bpy.context.scene.camera = camera

    constraint = camera.constraints.new(type="TRACK_TO")
    bpy.ops.object.empty_add(type="PLAIN_AXES", align="WORLD", location=(0, 0, 0))
    target = bpy.context.active_object
    target.name = "Camera_Target"

    constraint.target = target
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"

    return sun, camera


def set_linear_interpolation(obj: bpy.types.Object, data_path: str, index: int) -> None:
    """Force linear interpolation on a specific f-curve."""
    if not (obj.animation_data and obj.animation_data.action):
        return

    action = obj.animation_data.action
    fcurve = None

    if hasattr(action, "fcurve_ensure_for_datablock"):
        try:
            fcurve = action.fcurve_ensure_for_datablock(
                datablock=obj,
                data_path=data_path,
                index=index,
            )
        except Exception:
            pass

    if fcurve is None and hasattr(action, "fcurves"):
        for curve in action.fcurves:
            if curve.data_path == data_path and (index == -1 or curve.array_index == index):
                fcurve = curve
                break

    if fcurve:
        for keyframe in fcurve.keyframe_points:
            keyframe.interpolation = "LINEAR"


def create_animations(
    roof_obj: bpy.types.Object,
    panel_objects: list[bpy.types.Object],
    camera_obj: bpy.types.Object,
    sun_obj: bpy.types.Object,
) -> None:
    """Create the three-stage animation timeline."""
    scene = bpy.context.scene
    scene.frame_start = FRAME_START
    scene.frame_end = FRAME_END
    scene.frame_current = FRAME_START
    scene.render.fps = FPS

    for obj in [roof_obj, camera_obj, sun_obj] + panel_objects:
        if obj.animation_data:
            obj.animation_data_clear()

    roof_obj.scale = (0, 0, 0)
    roof_obj.keyframe_insert(data_path="scale", frame=1)
    roof_obj.scale = (1, 1, 1)
    roof_obj.keyframe_insert(data_path="scale", frame=20)

    panel_objects.sort(key=lambda panel: (panel.location.y, panel.location.x))

    for index, panel in enumerate(panel_objects):
        start_frame = 20 + index * 5
        end_frame = start_frame + 15

        panel.scale = (0, 0, 0)
        panel.keyframe_insert(data_path="scale", frame=1)
        panel.keyframe_insert(data_path="scale", frame=start_frame)
        panel.scale = (1, 1, 1)
        panel.keyframe_insert(data_path="scale", frame=end_frame)

    bpy.ops.object.empty_add(type="PLAIN_AXES", align="WORLD", location=(0, 0, 0))
    camera_rig = bpy.context.active_object
    camera_rig.name = "Camera_Rig"

    camera_obj.parent = camera_rig
    camera_obj.matrix_parent_inverse = camera_rig.matrix_world.inverted()

    camera_rig.rotation_euler.z = 0
    camera_rig.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
    camera_rig.keyframe_insert(data_path="rotation_euler", index=2, frame=120)

    camera_rig.rotation_euler.z = 2 * math.pi
    camera_rig.keyframe_insert(data_path="rotation_euler", index=2, frame=240)
    camera_rig.keyframe_insert(data_path="rotation_euler", index=2, frame=360)

    set_linear_interpolation(camera_rig, "rotation_euler", index=2)

    sun_data = sun_obj.data

    sun_obj.rotation_euler = (math.radians(-60), 0, math.radians(45))
    sun_obj.keyframe_insert(data_path="rotation_euler", frame=1)
    sun_obj.keyframe_insert(data_path="rotation_euler", frame=240)

    sun_obj.rotation_euler = (math.radians(0), 0, math.radians(45))
    sun_obj.keyframe_insert(data_path="rotation_euler", frame=300)

    sun_obj.rotation_euler = (math.radians(60), 0, math.radians(45))
    sun_obj.keyframe_insert(data_path="rotation_euler", frame=360)

    sun_data.energy = 1.0
    sun_data.keyframe_insert(data_path="energy", frame=1)
    sun_data.keyframe_insert(data_path="energy", frame=240)

    sun_data.energy = 5.0
    sun_data.keyframe_insert(data_path="energy", frame=300)

    sun_data.energy = 1.0
    sun_data.keyframe_insert(data_path="energy", frame=360)

    sun_data.color = (1.0, 0.7, 0.5)
    sun_data.keyframe_insert(data_path="color", frame=1)
    sun_data.keyframe_insert(data_path="color", frame=240)

    sun_data.color = (1.0, 1.0, 1.0)
    sun_data.keyframe_insert(data_path="color", frame=300)

    sun_data.color = (1.0, 0.6, 0.4)
    sun_data.keyframe_insert(data_path="color", frame=360)


def configure_gpu_devices(cycles_preferences: Any) -> None:
    """Enable all compatible GPU devices, preferring OptiX when available."""
    device_priority = ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI")
    cycles_preferences.refresh_devices()

    enabled_devices: list[Any] = []
    for device_type in device_priority:
        matching = [d for d in cycles_preferences.devices if d.type == device_type]
        if matching:
            cycles_preferences.compute_device_type = device_type
            enabled_devices = matching
            break

    if not enabled_devices:
        print("No GPU devices found. Cycles will fall back to CPU rendering.")
        return

    for device in cycles_preferences.devices:
        device.use = device in enabled_devices

    preferred = enabled_devices[0]
    print(f"Using Cycles GPU backend: {cycles_preferences.compute_device_type} ({preferred.name})")


def configure_render_settings() -> None:
    """Configure Cycles render, denoising, and output paths."""
    scene = bpy.context.scene
    script_dir = os.path.dirname(os.path.realpath(__file__))

    scene.render.engine = "CYCLES"
    scene.cycles.device = "GPU"
    scene.render.use_sequencer = False

    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = RENDER_NOISE_THRESHOLD
    scene.cycles.samples = RENDER_SAMPLES
    scene.cycles.adaptive_min_samples = 0

    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"

    scene.cycles.use_preview_adaptive_sampling = True
    scene.cycles.preview_adaptive_threshold = 0.1
    scene.cycles.preview_samples = VIEWPORT_SAMPLES

    try:
        scene.render.image_settings.media_type = 'VIDEO'
    except AttributeError:
        pass
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "HIGH"
    scene.render.filepath = os.path.join(script_dir, "..", "assets", "render", "solar_roof_")

    try:
        preferences = bpy.context.preferences
        cycles_preferences = preferences.addons["cycles"].preferences
        configure_gpu_devices(cycles_preferences)
    except Exception as exc:
        print(f"Could not configure GPU preferences: {exc}")


def main() -> None:
    """Generate the full solar roof scene."""
    print("Starting Blender Roof & Solar Panel Generation...")
    setup_scene()
    setup_world_lighting()
    configure_render_settings()
    materials = create_materials()

    roof_obj = build_roof(materials)
    panel_template = build_single_solar_panel_assembly(materials)
    panel_objects = place_solar_panels(panel_template)
    sun_obj, camera_obj = add_lighting_and_camera()
    create_animations(roof_obj, panel_objects, camera_obj, sun_obj)

    print("Generation complete!")


if __name__ == "__main__":
    main()
    if bpy.app.background:
        script_dir = os.path.dirname(os.path.realpath(__file__))
        filepath = os.path.join(script_dir, "solar_roof.blend")
        bpy.ops.wm.save_as_mainfile(filepath=filepath)
        print(f"Saved blend file to: {filepath}")