bl_info = {
    "name": "Quick Exports: Render Frames with Camera Names",
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
    
    cameras.sort(key=lambda cam: cam.name)
    start_frame = 0
    frame_step = 10
    
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
    scene.frame_step = 1
    
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
        
        split = layout.split(factor=0.40)  # Split the layout into two parts (55% - 45%)
        
        # Left column (titles)
        col = split.column()
        col.alignment = 'RIGHT'
        col.label(text="Naming")
        
        # Right column
        col = split.column()
        col.prop(scene, "use_camera_name", text="Use Camera Name")
        col.prop(scene, "strip_numbers", text="Strip Numbers")

        # Seperator
        layout.separator(factor=0.1)
        
        # Button
        layout.operator("render.bind_cameras_to_frames", text="Bind Cameras to Frames")



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
        default=False,
    )
    bpy.types.Scene.strip_numbers = bpy.props.BoolProperty(
        name="Cleanup Filenames",
        description="Remove numbers from camera names in the format 'Camera.001'",
        default=False,
    )
    bpy.app.handlers.render_complete.append(rename_rendered_frame)
    bpy.app.handlers.render_write.append(rename_rendered_frame)
    print("Handler registered")

def unregister():
    bpy.utils.unregister_class(RenderSettingsPanel)
    bpy.utils.unregister_class(BindCamerasOperator)
    del bpy.types.Scene.use_camera_name
    del bpy.types.Scene.strip_numbers
    bpy.app.handlers.render_complete.remove(rename_rendered_frame)
    bpy.app.handlers.render_write.remove(rename_rendered_frame)
    print("Handler unregistered")

if __name__ == "__main__":
    register()
