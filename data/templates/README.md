# Screen Monitoring Templates

This directory contains template images used for screen monitoring and UI element detection.

Required templates:
1. `play_button.png` - Template for video player play button
2. `next_button.png` - Template for course navigation next button

## Template Requirements

- Images should be PNG format
- Capture only the specific UI element with minimal surrounding area
- Use consistent resolution across templates
- Ensure good contrast between the element and background
- Test templates with different themes/color schemes if applicable

## Creating Templates

1. Take a screenshot of the course platform
2. Crop the image to isolate the UI element
3. Save as PNG in this directory
4. Update the confidence threshold in `config/courses.yaml` if needed

## Current Templates

- [ ] play_button.png (Pending)
- [ ] next_button.png (Pending)

Note: These templates need to be created for each course platform separately if their UI elements differ significantly. 