#!/usr/bin/env python3
"""
Create social image for Cert Me Boi GitHub repository
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_social_image():
    """Create a social image for the repository"""
    
    # Create a 1200x630 image (GitHub social media recommended size)
    width, height = 1200, 630
    image = Image.new('RGB', (width, height), color='#0d1117')  # GitHub dark theme
    
    draw = ImageDraw.Draw(image)
    
    # Try to load a font, fallback to default if not available
    try:
        # Try to use a system font
        title_font = ImageFont.truetype("arial.ttf", 72)
        subtitle_font = ImageFont.truetype("arial.ttf", 36)
        body_font = ImageFont.truetype("arial.ttf", 24)
    except:
        # Fallback to default font
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
    
    # Draw gradient background
    for y in range(height):
        # Create a subtle gradient from dark to slightly lighter
        r = int(13 + (y / height) * 10)
        g = int(17 + (y / height) * 10)
        b = int(23 + (y / height) * 10)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Draw main title
    title = "🎓 Cert Me Boi"
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (width - title_width) // 2
    title_y = 100
    
    # Draw title with glow effect
    for offset in range(3):
        draw.text((title_x + offset, title_y + offset), title, 
                  font=title_font, fill='#f0f6fc')
    
    # Draw subtitle
    subtitle = "Automated Course Certification System"
    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_x = (width - subtitle_width) // 2
    subtitle_y = title_y + 100
    
    draw.text((subtitle_x, subtitle_y), subtitle, 
              font=subtitle_font, fill='#7d8590')
    
    # Draw feature highlights
    features = [
        "🤖 AI-Powered Automation",
        "🎯 Multi-Platform Support", 
        "🖥️ Beautiful Web Interface",
        "🔧 Advanced Error Recovery"
    ]
    
    feature_y = subtitle_y + 120
    for i, feature in enumerate(features):
        feature_x = 100 + (i % 2) * 500
        feature_y_pos = feature_y + (i // 2) * 60
        
        draw.text((feature_x, feature_y_pos), feature, 
                  font=body_font, fill='#e6edf3')
    
    # Draw bottom text
    bottom_text = "Free • Open Source • Python"
    bottom_bbox = draw.textbbox((0, 0), bottom_text, font=body_font)
    bottom_width = bottom_bbox[2] - bottom_bbox[0]
    bottom_x = (width - bottom_width) // 2
    bottom_y = height - 80
    
    draw.text((bottom_x, bottom_y), bottom_text, 
              font=body_font, fill='#7d8590')
    
    # Draw decorative elements
    # Top left corner accent
    draw.rectangle([(0, 0), (50, 50)], fill='#238636', outline='#238636')
    
    # Bottom right corner accent  
    draw.rectangle([(width-50, height-50), (width, height)], 
                   fill='#238636', outline='#238636')
    
    # Save the image
    output_path = "cert-me-boi-social.png"
    image.save(output_path, "PNG")
    print(f"Social image created: {output_path}")
    
    return output_path

if __name__ == "__main__":
    create_social_image() 