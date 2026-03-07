import os
import re

lib_dir = r"d:\Research\zip skin\Reserch_Skin-care-deseases\app\lib"

# Mappings for AppColors string replacement
color_replacements = {
    "AppColors.primary": "AppColors.primary", # unchanged
    "AppColors.primaryLight": "AppColors.primaryLight", # unchanged 
    "AppColors.primaryDark": "AppColors.primaryDark", # unchanged
    "AppColors.secondary": "AppColors.secondary",
    "AppColors.accent": "AppColors.accent",
    "AppColors.highlight": "AppColors.highlight",
    "AppColors.success": "AppColors.success",
    "AppColors.warning": "AppColors.warning",
    "AppColors.error": "AppColors.error",
    
    # Theme dynamic colors
    "AppColors.surfaceGlass": "context.clrSurfaceGlass",
    "AppColors.surface": "context.clrSurface",
    "AppColors.backgroundAlt": "context.clrBackgroundAlt",
    "AppColors.background": "context.clrBackground",
    "AppColors.textMain": "context.clrTextMain",
    "AppColors.textSecondary": "context.clrTextSec",
    "AppColors.border": "context.clrBorder",
}

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # If already refactored, skip
    # if "context.clr" in content and filepath.endswith("app_styles.dart") == False:
    #    return

    original_content = content

    # 1. Remove `const ` before widgets/components using these colors, since they're dynamic now
    # We'll blindly remove `const ` before `AppTextStyles`, `TextStyle`, `BoxDecoration`, `Color`, `BorderSide`
    # This is a bit brute force but effective for Flutter
    content = re.sub(r'const\s+(TextStyle\(.*?AppColors\.(textMain|textSecondary|border).*?\))', r'\1', content, flags=re.DOTALL)
    content = re.sub(r'const\s+(BoxDecoration\(.*?AppColors\.(surface|background).*?\))', r'\1', content, flags=re.DOTALL)
    
    # Handle AppTextStyles
    # Change `AppTextStyles.heading` -> `AppTextStyles.heading(context)`
    # Only if it doesn't already have (context)
    styles = ['heading', 'subHeading', 'body', 'bodyStrong', 'caption']
    for style in styles:
        # Match `AppTextStyles.heading` not followed by `(` or matching `const AppTextStyles.heading`
        content = re.sub(fr'const\s+AppTextStyles\.{style}', fr'AppTextStyles.{style}(context)', content)
        content = re.sub(fr'AppTextStyles\.{style}(?!\()', fr'AppTextStyles.{style}(context)', content)

    # Handle AppDecor
    content = re.sub(r'AppDecor\.softCard\(', r'AppDecor.softCard(context, ', content)
    content = re.sub(r'AppDecor\.glassCard\(', r'AppDecor.glassCard(context, ', content)
    content = re.sub(r'AppGradients\.page', r'AppGradients.page(context)', content)

    # Clean up orphaned consts due to the replacements (like `const Text('Hello', style: AppTextStyles.body(context))`)
    # `const Text` -> `Text` if it contains `context`
    # We will do a generic pass: if `const` is followed by something that eventually has `context` before a closing brace, it's rough. Let's just remove `const ` if the line has `context.` or `context)`
    lines = content.split('\n')
    for i in range(len(lines)):
        if "context" in lines[i] and "const " in lines[i]:
            lines[i] = lines[i].replace("const ", "")
    content = '\n'.join(lines)

    # 2. Replace colors
    for old_color, new_color in color_replacements.items():
        if "context." in new_color:
            content = content.replace(old_color, new_color)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Refactored: {filepath}")

for root, dirs, files in os.walk(lib_dir):
    for file in files:
        if file.endswith('.dart') and file != "app_styles.dart":
            process_file(os.path.join(root, file))

print("DONE")
