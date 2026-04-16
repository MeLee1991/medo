import gradio as gr
from PIL import Image, ImageOps
import zipfile
import io

# Base Dimensions at 300 DPI (Portrait: Width x Height)
DIMENSIONS = {
    "A3": (3508, 4960),
    "A4": (2480, 3508),
    "A5": (1748, 2480),
    "B4": (2953, 4169),
    "B5": (2079, 2953),
    "US Letter": (2550, 3300),
    "US Legal": (2550, 4200),
    "US Tabloid": (3300, 5100),
    "US Half Letter": (1650, 2550),
    "Poster 11x14": (3300, 4200),
    "Poster 18x24": (5400, 7200),
    "Poster 24x36": (7200, 10800)
}

def process_images(input_img, selected_sizes, formats, strategy, orientation):
    if not input_img or not selected_sizes or not formats:
        return None
    
    zip_path = "printable_package.zip"
    
    with zipfile.ZipFile(zip_path, "w") as zf:
        for display_name in selected_sizes:
            width, height = DIMENSIONS[display_name]
            
            # Swap dimensions if Landscape is selected
            if orientation == "Landscape":
                target_size = (height, width)
            else:
                target_size = (width, height)
            
            # 1. Resize based on Strategy
            if strategy == "Crop (Fill Canvas)":
                resized = ImageOps.fit(input_img, target_size, Image.Resampling.LANCZOS)
            else:
                resized = ImageOps.pad(input_img, target_size, Image.Resampling.LANCZOS, color=(255, 255, 255))
            
            # 2. Save requested formats
            for fmt in formats:
                buffer = io.BytesIO()
                final_img = resized.convert("RGB") if fmt in ["JPG", "PDF"] else resized
                
                if fmt == "PDF":
                    final_img.save(buffer, format="PDF", resolution=300.0)
                elif fmt == "JPG":
                    final_img.save(buffer, format="JPEG", quality=95)
                else:
                    final_img.save(buffer, format="PNG")
                
                zf.writestr(f"{display_name}_{orientation}.{fmt.lower()}", buffer.getvalue())
                
    return zip_path

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎨 The Global Printable Factory")
    
    with gr.Row():
        with gr.Column(scale=1):
            img_input = gr.Image(type="pil", label="Upload High-Res Master")
            
            orientation = gr.Radio(
                ["Portrait", "Landscape"], 
                label="4. Orientation", 
                value="Portrait",
                info="Swaps width and height automatically."
            )
            
            formats = gr.CheckboxGroup(["PNG", "JPG", "PDF"], label="Export Formats", value=["PNG", "PDF"])
            
            strategy = gr.Radio(
                ["Crop (Fill Canvas)", "Pad (White Borders)"], 
                label="Aspect Ratio Strategy", 
                value="Pad (White Borders)"
            )

        with gr.Column(scale=1):
            size_list = gr.CheckboxGroup(
                choices=list(DIMENSIONS.keys()), 
                label="Select Target Sizes",
                value=["A3", "A4", "US Letter"]
            )
            
            with gr.Row():
                select_all = gr.Button("Select All")
                deselect_all = gr.Button("Clear All")

            run_btn = gr.Button("🚀 Generate ZIP Package", variant="primary")
            file_output = gr.File(label="Download Your ZIP")

    select_all.click(lambda: list(DIMENSIONS.keys()), outputs=size_list)
    deselect_all.click(lambda: [], outputs=size_list)
    
    run_btn.click(
        fn=process_images, 
        inputs=[img_input, size_list, formats, strategy, orientation], 
        outputs=file_output
    )

demo.launch()
