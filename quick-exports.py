bl_info = {
    "name": "Render Frames with Camera Names",
    "blender": (2, 80, 0),
    "category": "Render",
}

import bpy
import os
import re

def rename_rendered_frame(scene):
    if not scene.use_camera_name:
        return
    
    camera = scene.camera
    output_dir = bpy.context.scene.render.filepath
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    camera_name = camera.name
    if scene.strip_numbers:
        camera_name = re.sub(r"\.\d{3}$", "", camera_name)

    # Check if the filename already exists
    output_path = os.path.join(output_dir, f"{camera_name}.png")
    counter = 1
    while os.path.exists(output_path):
        output_path = os.path.join(output_dir, f"{camera_name} {counter}.png")
        counter += 1
    
    # Get the default output filename
    default_output_path = bpy.context.scene.render.frame_path(frame=scene.frame_current)
    
    # Rename the rendered image to the desired filename
    os.rename(default_output_path, output_path)
    
    print(f"Renamed frame for camera: {camera_name}")

def bind_cameras_to_frames(scene):
    print("bind_cameras_to_frames called")
    
    cameras = [obj for obj in scene.objects if obj.type == 'CAMERA']
    if not cameras:
        print("No cameras found in the scene")
        return

    # Remove existing camera binds and markers if the option is enabled
    if scene.remove_existing_binds:
        scene.timeline_markers.clear()
        for marker in scene.timeline_markers:
            if marker.camera:
                marker.camera = None
    
    cameras.sort(key=lambda cam: cam.name)
    start_frame = 0
    frame_step = scene.frame_gap
    
    for i, camera in enumerate(cameras):
        frame = start_frame + i * frame_step
        scene.frame_set(frame)
        scene.camera = camera
        
        # Create a new marker
        marker = bpy.data.scenes[scene.name].timeline_markers.new(name=camera.name, frame=frame)
        
        # Bind the camera to the marker
        marker.camera = camera
    
    scene.frame_start = start_frame
    scene.frame_end = start_frame + (len(cameras) - 1) * frame_step
    if scene.use_frame_gap_as_step:
        scene.frame_step = frame_step
    
    print("Cameras bound to frames and frame range adjusted")


class RenderSettingsPanel(bpy.types.Panel):
    bl_label = "Output Settings"
    bl_idname = "RENDER_PT_output_settings"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "output"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Use a single column layout for the entire panel
        col = layout.column()
        
        # File Naming section
        naming_split = col.split(factor=0.40)
        naming_title_col = naming_split.column()
        naming_title_col.alignment = 'RIGHT'
        naming_title_col.label(text="File Naming")
        naming_col = naming_split.column()
        naming_col.prop(scene, "use_camera_name", text="Use Camera Name")
        naming_col.prop(scene, "strip_numbers", text="Strip Numbers")
        
        # Frame Gap section
        frame_gap_split = col.split(factor=0.40)
        frame_gap_title_col = frame_gap_split.column()
        frame_gap_title_col.alignment = 'RIGHT'
        frame_gap_title_col.label(text="Frame Gap")
        frame_gap_col = frame_gap_split.column()
        frame_gap_col.prop(scene, "frame_gap", text="")
        frame_gap_col.prop(scene, "use_frame_gap_as_step", text="Use Frame Gap as Frame Step")
        frame_gap_col.prop(scene, "remove_existing_binds", text="Remove Existing Binds and Markers")
        
        # Separator for visual separation
        col.separator(factor=0.1)
        
        # Button
        col.operator("render.bind_cameras_to_frames", text="Bind Cameras to Frames")


class BindCamerasOperator(bpy.types.Operator):
    bl_idname = "render.bind_cameras_to_frames"
    bl_label = "Bind Cameras to Frames"
    
    def execute(self, context):
        print("BindCamerasOperator execute called")
        bind_cameras_to_frames(context.scene)
        return {'FINISHED'}

def register():
    bpy.utils.register_class(RenderSettingsPanel)
    bpy.utils.register_class(BindCamerasOperator)
    bpy.types.Scene.use_camera_name = bpy.props.BoolProperty(
        name="Use Camera Name",
        description="Save rendered frames with the camera name",
        default=True,
    )
    bpy.types.Scene.strip_numbers = bpy.props.BoolProperty(
        name="Cleanup Filenames",
        description="Remove numbers from camera names in the format 'Camera.001'",
        default=True,
    )
    bpy.types.Scene.frame_gap = bpy.props.IntProperty(
        name="Frame Gap",
        description="Number of frames between each camera bind",
        default=10,
        min=1
    )
    bpy.types.Scene.use_frame_gap_as_step = bpy.props.BoolProperty(
        name="Use Frame Gap as Frame Step",
        description="Use the frame gap value as the frame step for the animation",
        default=True,
    )
    bpy.types.Scene.remove_existing_binds = bpy.props.BoolProperty(
        name="Remove Existing Binds and Markers",
        description="Remove any existing camera binds and markers before binding new ones",
        default=True,
    )
    bpy.app.handlers.render_complete.append(rename_rendered_frame)
    bpy.app.handlers.render_write.append(rename_rendered_frame)
    print("Handler registered")

def unregister():
    bpy.utils.unregister_class(RenderSettingsPanel)
    bpy.utils.unregister_class(BindCamerasOperator)
    del bpy.types.Scene.use_camera_name
    del bpy.types.Scene.strip_numbers
    del bpy.types.Scene.frame_gap
    del bpy.types.Scene.use_frame_gap_as_step
    del bpy.types.Scene.remove_existing_binds
    bpy.app.handlers.render_complete.remove(rename_rendered_frame)
    bpy.app.handlers.render_write.remove(rename_rendered_frame)
    print("Handler unregistered")

if __name__ == "__main__":
    register()
