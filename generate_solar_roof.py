import bpy
import math

def setup_scene():
    # Delete all objects (meshes, curves, lights, cameras, empties, etc.) to start fresh
    for obj in list(bpy.data.objects):
        try:
            bpy.data.objects.remove(obj, do_unlink=True)
        except Exception as e:
            print(f"Failed to remove object {obj.name}: {e}")
    
    # Delete all materials
    for material in list(bpy.data.materials):
        try:
            bpy.data.materials.remove(material, do_unlink=True)
        except Exception as e:
            print(f"Failed to remove material {material.name}: {e}")

def create_materials():
    materials = {}
    
    # --- Roof Concrete Material ---
    mat_roof = bpy.data.materials.new(name="Concrete_Roof")
    mat_roof.use_nodes = True
    nodes = mat_roof.node_tree.nodes
    principled = nodes.get("Principled BSDF")
    if principled:
        principled.inputs['Base Color'].default_value = (0.3, 0.3, 0.32, 1.0) # Grey
        principled.inputs['Roughness'].default_value = 0.8
        principled.inputs['Metallic'].default_value = 0.0
    materials['roof'] = mat_roof

    # --- Aluminium Frame Material ---
    mat_frame = bpy.data.materials.new(name="Aluminium_Frame")
    mat_frame.use_nodes = True
    nodes = mat_frame.node_tree.nodes
    principled = nodes.get("Principled BSDF")
    if principled:
        principled.inputs['Base Color'].default_value = (0.7, 0.7, 0.72, 1.0) # Silver-grey
        principled.inputs['Metallic'].default_value = 0.95
        principled.inputs['Roughness'].default_value = 0.25
    materials['frame'] = mat_frame

    # --- Galvanized Steel Rack Material ---
    mat_rack = bpy.data.materials.new(name="Galvanized_Rack")
    mat_rack.use_nodes = True
    nodes = mat_rack.node_tree.nodes
    principled = nodes.get("Principled BSDF")
    if principled:
        principled.inputs['Base Color'].default_value = (0.5, 0.52, 0.53, 1.0) # Medium metallic grey
        principled.inputs['Metallic'].default_value = 0.8
        principled.inputs['Roughness'].default_value = 0.4
    materials['rack'] = mat_rack

    # --- Glossy Silicon Solar Cell Material (with Grid Texture) ---
    mat_silicon = bpy.data.materials.new(name="Silicon_Cells")
    mat_silicon.use_nodes = True
    nodes = mat_silicon.node_tree.nodes
    links = mat_silicon.node_tree.links
    
    # Clear default nodes to build a custom shader
    nodes.clear()
    
    # Create nodes
    node_output = nodes.new(type='ShaderNodeOutputMaterial')
    node_principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_tex_coord = nodes.new(type='ShaderNodeTexCoord')
    node_mapping = nodes.new(type='ShaderNodeMapping')
    node_brick = nodes.new(type='ShaderNodeTexBrick')
    
    # Configure Brick Texture for Solar Cells Grid
    node_brick.offset = 0.0
    node_brick.offset_frequency = 1
    # Scale of the grid
    node_brick.inputs['Scale'].default_value = 15.0
    node_brick.inputs['Mortar Size'].default_value = 0.015
    node_brick.inputs['Mortar Smooth'].default_value = 0.0
    node_brick.inputs['Row Height'].default_value = 1.0
    node_brick.inputs['Brick Width'].default_value = 1.0
    
    # Colors for Brick Texture
    # Color1 & Color2: Deep Glossy Blue/Black (Silicon)
    node_brick.inputs['Color1'].default_value = (0.02, 0.04, 0.1, 1.0)
    node_brick.inputs['Color2'].default_value = (0.02, 0.04, 0.1, 1.0)
    # Mortar Color: Silver grid lines
    node_brick.inputs['Mortar'].default_value = (0.6, 0.6, 0.65, 1.0)
    
    # Setup node mapping
    links.new(node_tex_coord.outputs['Generated'], node_mapping.inputs['Vector'])
    links.new(node_mapping.outputs['Vector'], node_brick.inputs['Vector'])
    links.new(node_brick.outputs['Color'], node_principled.inputs['Base Color'])
    
    # Configure Principled BSDF for Silicon
    node_principled.inputs['Roughness'].default_value = 0.08
    node_principled.inputs['Metallic'].default_value = 0.1
    # Specular IOR Level in 4.0+, Specular in 3.x
    if 'Specular' in node_principled.inputs:
        node_principled.inputs['Specular'].default_value = 0.9
    elif 'Specular IOR Level' in node_principled.inputs:
        node_principled.inputs['Specular IOR Level'].default_value = 0.9
        
    links.new(node_principled.outputs['BSDF'], node_output.inputs['Surface'])
    materials['silicon'] = mat_silicon

    return materials

def build_roof(materials, length=9.66, width=6.23, thickness=0.3):
    # Create the main flat roof block
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -thickness/2))
    roof_obj = bpy.context.active_object
    roof_obj.name = "Concrete_Roof_Slab"
    roof_obj.dimensions = (length, width, thickness)
    
    # Apply Scale
    bpy.ops.object.transform_apply(scale=True)
    
    # Assign concrete material
    if roof_obj.data.materials:
        roof_obj.data.materials[0] = materials['roof']
    else:
        roof_obj.data.materials.append(materials['roof'])
        
    return roof_obj

def build_single_solar_panel_assembly(materials, width=1.70, length=1.00, thickness=0.04, tilt_angle_deg=15):
    # We will build a solar panel assembly at (0,0,0) and join its parts.
    # The assembly consists of:
    # 1. Aluminium Frame
    # 2. Silicon Plate
    # 3. Support Rack (Metal triangles on the sides + legs)
    
    parts_to_join = []
    
    # --- 1. Create Frame ---
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
    frame_obj = bpy.context.active_object
    frame_obj.name = "Panel_Frame"
    frame_obj.dimensions = (width, length, thickness)
    bpy.ops.object.transform_apply(scale=True)
    frame_obj.data.materials.append(materials['frame'])
    parts_to_join.append(frame_obj)
    
    # --- 2. Create Silicon Face ---
    silicon_w = width - 0.04
    silicon_l = length - 0.04
    silicon_t = 0.01
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, (thickness/2) - (silicon_t/2) + 0.002))
    silicon_obj = bpy.context.active_object
    silicon_obj.name = "Panel_Silicon"
    silicon_obj.dimensions = (silicon_w, silicon_l, silicon_t)
    bpy.ops.object.transform_apply(scale=True)
    silicon_obj.data.materials.append(materials['silicon'])
    parts_to_join.append(silicon_obj)
    
    # --- 3. Create Support Brackets (Rack) ---
    # We build the support rack under the panel before we tilt it.
    angle_rad = math.radians(tilt_angle_deg)
    
    clearance = 0.15 # Height of panel center above the roof
    
    leg_x_offsets = [-width/2 + 0.15, width/2 - 0.15]
    back_y = length/2 - 0.05
    front_y = -length/2 + 0.05
    
    z_offset_local = -thickness/2
    
    # Back leg position in world space after tilt:
    back_y_world = back_y * math.cos(angle_rad) - z_offset_local * math.sin(angle_rad)
    back_z_world = back_y * math.sin(angle_rad) + z_offset_local * math.cos(angle_rad) + clearance
    
    # Front leg position in world space after tilt:
    front_y_world = front_y * math.cos(angle_rad) - z_offset_local * math.sin(angle_rad)
    front_z_world = front_y * math.sin(angle_rad) + z_offset_local * math.cos(angle_rad) + clearance
    
    # Create the Back Legs (Steel square tubes)
    for x in leg_x_offsets:
        leg_h = back_z_world
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, back_y_world, leg_h/2 - (thickness/2)))
        leg = bpy.context.active_object
        leg.name = "Rack_Leg_Back"
        leg.dimensions = (0.04, 0.04, leg_h)
        bpy.ops.object.transform_apply(scale=True)
        leg.data.materials.append(materials['rack'])
        parts_to_join.append(leg)
        
    # Create the Front Legs (Shorter steel tubes)
    for x in leg_x_offsets:
        leg_h = front_z_world
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, front_y_world, leg_h/2 - (thickness/2)))
        leg = bpy.context.active_object
        leg.name = "Rack_Leg_Front"
        leg.dimensions = (0.04, 0.04, leg_h)
        bpy.ops.object.transform_apply(scale=True)
        leg.data.materials.append(materials['rack'])
        parts_to_join.append(leg)

    # Create diagonal support bars connecting front and back legs
    for x in leg_x_offsets:
        dy = back_y_world - front_y_world
        dz = back_z_world - front_z_world
        beam_len = math.sqrt(dy**2 + dz**2)
        beam_angle = math.atan2(dz, dy)
        
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, (back_y_world + front_y_world)/2, (back_z_world + front_z_world)/2 - (thickness/2)))
        beam = bpy.context.active_object
        beam.name = "Rack_Beam_Diagonal"
        beam.dimensions = (0.03, beam_len, 0.03)
        beam.rotation_euler[0] = beam_angle
        bpy.ops.object.transform_apply(scale=True, rotation=True)
        beam.data.materials.append(materials['rack'])
        parts_to_join.append(beam)

    # Now, tilt the Frame and Silicon and position them.
    frame_obj.rotation_euler[0] = angle_rad
    frame_obj.location = (0, 0, clearance)
    bpy.ops.object.select_all(action='DESELECT')
    frame_obj.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    
    silicon_obj.rotation_euler[0] = angle_rad
    offset_z = (thickness/2) - (silicon_t/2) + 0.002
    silicon_y_world = -offset_z * math.sin(angle_rad)
    silicon_z_world = offset_z * math.cos(angle_rad) + clearance
    silicon_obj.location = (0, silicon_y_world, silicon_z_world)
    bpy.ops.object.select_all(action='DESELECT')
    silicon_obj.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Join all parts
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts_to_join:
        p.select_set(True)
    
    bpy.context.view_layer.objects.active = frame_obj
    bpy.ops.object.join()
    
    panel_assembly = bpy.context.active_object
    panel_assembly.name = "Solar_Panel_Assembly"
    
    return panel_assembly

def place_solar_panels(panel_template, roof_length=9.66, roof_width=6.23, panel_width=1.70, panel_length=1.00, tilt_angle_deg=15):
    num_cols = 5
    num_rows = 3
    
    col_gap = 0.03
    row_pitch = 1.6
    
    row_width_total = num_cols * panel_width + (num_cols - 1) * col_gap
    start_x = -row_width_total / 2 + panel_width / 2
    row_layout_depth = (num_rows - 1) * row_pitch
    start_y = -row_layout_depth / 2
    
    panels_group = bpy.data.collections.new("Solar_Panels")
    bpy.context.scene.collection.children.link(panels_group)
    
    panel_objects = []
    first_panel = True
    
    for r in range(num_rows):
        y_pos = start_y + r * row_pitch
        for c in range(num_cols):
            x_pos = start_x + c * (panel_width + col_gap)
            
            if first_panel:
                panel_template.location = (x_pos, y_pos, 0)
                try:
                    bpy.context.scene.collection.objects.unlink(panel_template)
                except:
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

def add_lighting_and_camera(roof_length=9.66, roof_width=6.23):
    # Add Sun light
    bpy.ops.object.light_add(type='SUN', radius=1, align='WORLD', location=(5, -5, 10))
    sun = bpy.context.active_object
    sun.name = "Sun_Light"
    sun.data.energy = 4.0
    sun.rotation_euler = (math.radians(45), 0, math.radians(30))
    
    # Add Camera
    bpy.ops.object.camera_add(align='WORLD', location=(10, -12, 8))
    camera = bpy.context.active_object
    camera.name = "View_Camera"
    
    constraint = camera.constraints.new(type='TRACK_TO')
    bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, 0, 0))
    target = bpy.context.active_object
    target.name = "Camera_Target"
    
    constraint.target = target
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'
    
    return sun, camera

def set_linear_interpolation(obj, data_path, index):
    if not (obj.animation_data and obj.animation_data.action):
        return
    action = obj.animation_data.action
    fcurve = None
    
    # Try Blender 5.0+ method
    if hasattr(action, "fcurve_ensure_for_datablock"):
        try:
            fcurve = action.fcurve_ensure_for_datablock(datablock=obj, data_path=data_path, index=index)
        except Exception:
            pass
            
    # Try Blender 4.x / 3.x method
    if fcurve is None and hasattr(action, "fcurves"):
        for fc in action.fcurves:
            if fc.data_path == data_path and (index == -1 or fc.array_index == index):
                fcurve = fc
                break
                
    if fcurve:
        for kp in fcurve.keyframe_points:
            kp.interpolation = 'LINEAR'

def create_animations(roof_obj, panel_objects, camera_obj, sun_obj):
    # Set the timeline settings
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 360
    scene.frame_current = 1
    scene.render.fps = 30
    
    # Clear any existing animation data
    for obj in [roof_obj, camera_obj, sun_obj] + panel_objects:
        if obj.animation_data:
            obj.animation_data_clear()

    # --- 1. Roof Slab Assembly (Frames 1-20) ---
    # Frame 1: Scale is 0
    roof_obj.scale = (0, 0, 0)
    roof_obj.keyframe_insert(data_path="scale", frame=1)
    # Frame 20: Scale is 1
    roof_obj.scale = (1, 1, 1)
    roof_obj.keyframe_insert(data_path="scale", frame=20)
    
    # --- 2. Solar Panels Staggered Assembly (Frames 20-110) ---
    # Sort panels by their position so they assemble in a neat sequence
    # Left-to-right (X), bottom-to-top (Y)
    panel_objects.sort(key=lambda p: (p.location.y, p.location.x))
    
    for i, panel in enumerate(panel_objects):
        start_frame = 20 + i * 5 # Staggered offset
        end_frame = start_frame + 15
        
        # Frame 1: Scale is 0 (keep invisible)
        panel.scale = (0, 0, 0)
        panel.keyframe_insert(data_path="scale", frame=1)
        panel.keyframe_insert(data_path="scale", frame=start_frame)
        
        # end_frame: Scale is 1
        panel.scale = (1, 1, 1)
        panel.keyframe_insert(data_path="scale", frame=end_frame)

    # --- 3. Camera Orbit (Frames 120-240) ---
    # Add parent Empty at (0, 0, 0) for camera rotation
    bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, 0, 0))
    camera_rig = bpy.context.active_object
    camera_rig.name = "Camera_Rig"
    
    # Parent camera to rig without moving it
    camera_obj.parent = camera_rig
    camera_obj.matrix_parent_inverse = camera_rig.matrix_world.inverted()
    
    # Animate Z rotation of the rig
    camera_rig.rotation_euler.z = 0
    camera_rig.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
    camera_rig.keyframe_insert(data_path="rotation_euler", index=2, frame=120)
    
    camera_rig.rotation_euler.z = 2 * math.pi
    camera_rig.keyframe_insert(data_path="rotation_euler", index=2, frame=240)
    camera_rig.keyframe_insert(data_path="rotation_euler", index=2, frame=360)
    
    # Make rotation linear
    set_linear_interpolation(camera_rig, "rotation_euler", index=2)
                    
    # --- 4. Sun Study (Frames 240-360) ---
    sun_data = sun_obj.data
    
    # Animate sun rotation (sweep from east/morning to west/evening)
    sun_obj.rotation_euler = (math.radians(-60), 0, math.radians(45))
    sun_obj.keyframe_insert(data_path="rotation_euler", frame=1)
    sun_obj.keyframe_insert(data_path="rotation_euler", frame=240)
    
    sun_obj.rotation_euler = (math.radians(0), 0, math.radians(45))
    sun_obj.keyframe_insert(data_path="rotation_euler", frame=300)
    
    sun_obj.rotation_euler = (math.radians(60), 0, math.radians(45))
    sun_obj.keyframe_insert(data_path="rotation_euler", frame=360)
    
    # Animate sun energy (intensity)
    sun_data.energy = 1.0
    sun_data.keyframe_insert(data_path="energy", frame=1)
    sun_data.keyframe_insert(data_path="energy", frame=240)
    
    sun_data.energy = 5.0
    sun_data.keyframe_insert(data_path="energy", frame=300)
    
    sun_data.energy = 1.0
    sun_data.keyframe_insert(data_path="energy", frame=360)
    
    # Animate sun color (warm dawn -> bright midday -> warm sunset)
    sun_data.color = (1.0, 0.7, 0.5)
    sun_data.keyframe_insert(data_path="color", frame=1)
    sun_data.keyframe_insert(data_path="color", frame=240)
    
    sun_data.color = (1.0, 1.0, 1.0)
    sun_data.keyframe_insert(data_path="color", frame=300)
    
    sun_data.color = (1.0, 0.6, 0.4)
    sun_data.keyframe_insert(data_path="color", frame=360)

def configure_render_settings():
    scene = bpy.context.scene
    
    # 1. Set render engine to Cycles and GPU compute
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    
    # 2. Optimize Render sampling settings (high speed, good quality with denoising)
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.05  # Noise Threshold: 0.05 (fast, clean with denoise)
    scene.cycles.samples = 256              # Max Samples: 256 (instead of 4096)
    scene.cycles.adaptive_min_samples = 0   # Let Cycles choose min samples automatically
    
    # 3. Enable Render Denoising
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    
    # 4. Optimize Viewport sampling settings for smooth interactive work
    scene.cycles.use_preview_adaptive_sampling = True
    scene.cycles.preview_adaptive_threshold = 0.1
    scene.cycles.preview_samples = 128
    
    # 5. Optimize Blender Preferences for RTX 3050 (OptiX backend)
    try:
        preferences = bpy.context.preferences
        cycles_preferences = preferences.addons['cycles'].preferences
        cycles_preferences.compute_device_type = 'OPTIX'
        cycles_preferences.refresh_devices()
        
        for device in cycles_preferences.devices:
            if device.type == 'OPTIX' and "3050" in device.name:
                device.use = True
            else:
                device.use = False
    except Exception as e:
        print(f"Could not optimize system device preferences: {e}")

def main():
    print("Starting Blender Roof & Solar Panel Generation...")
    setup_scene()
    configure_render_settings()
    materials = create_materials()
    
    # Roof parameters (matching 60.18 sq.m area and 31.78m perimeter)
    roof_l = 9.66
    roof_w = 6.23
    roof_thickness = 0.3
    
    roof_obj = build_roof(materials, length=roof_l, width=roof_w, thickness=roof_thickness)
    
    panel_template = build_single_solar_panel_assembly(
        materials, 
        width=1.70, 
        length=1.00, 
        thickness=0.04, 
        tilt_angle_deg=15
    )
    
    panel_objects = place_solar_panels(
        panel_template, 
        roof_length=roof_l, 
        roof_width=roof_w, 
        panel_width=1.70, 
        panel_length=1.00,
        tilt_angle_deg=15
    )
    
    sun_obj, camera_obj = add_lighting_and_camera(roof_length=roof_l, roof_width=roof_w)
    
    create_animations(roof_obj, panel_objects, camera_obj, sun_obj)
    
    print("Generation complete!")

if __name__ == "__main__":
    main()
    if bpy.app.background:
        import os
        script_dir = os.path.dirname(os.path.realpath(__file__))
        filepath = os.path.join(script_dir, "solar_roof.blend")
        bpy.ops.wm.save_as_mainfile(filepath=filepath)
        print(f"Saved blend file to: {filepath}")
