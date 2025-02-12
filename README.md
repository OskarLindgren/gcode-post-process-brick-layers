#### Made with Love & Code by Oskar Lindgren


----------
# This project is at EoL, for futher work see [This PR for Orca Slicer](https://github.com/SoftFever/OrcaSlicer/pull/8181)

----------

# Brick Layering G-code Post-Processing Script

This project implements a **crude "brick layering" post-processing script** for G-code files generated by [Orca Slicer](https://github.com/SoftFever/OrcaSlicer). The script modifies inner wall paths in G-code to create a staggered or "bricked" pattern, potentially improving print strength. 

**License:** [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/)

---

## **Notes**
- Make sure the filament you're using in Orca slicer has `Don't slow outer walls` enabled under the `cooling` section, this could potentially cause artifacts with brick layers
- It's highly recomended to set `wall_sequence` (aka "Walls printing order) to "Outer/Inner", this avoids many potential issues
- Arc fitting is not supported and will not work

## **Features**
- Reads G-code files generated by Orca Slicer.
- Identifies key slicer settings from the G-code comments (e.g., layer height, wall count, wall sequence).
- Adjusts Z-coordinates dynamically to create a staggered "brick" effect on inner walls.
- Outputs a modified G-code file (`edited.gcode`).

### **Known Bugs**
- When the number of wall loops is even and wall order is set to "inner-outer-inner", the staggering pattern isn't applied correctly to all walls. (the 2 outer-most inner walls both have bricking applied). This is due to incomplete handling of wall print sequence logic.
- Walls are still printed based on position in xy plane, so if the nozzle has a large surface around the opening, that will cause the raised layer to be flattened down to some degree, it's unclear if this makes the part weaker or stronger, more testing is needed ***(A FIX FOR THIS US LIKELY TO BE FIXED 2025-01-11 OR 2025-01-12, the issue is known and a solution is in the works)***
- **Non-Specific Known Issue:**
- Some slicer settings might break the script.
- G0 moves are not supported, please ensure that travel moves are G1 moves
---

## **Requirements**
- Python 3.8+
- A G-code file generated by Orca Slicer.

---

## **Usage**

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/brick-layering-script.git
   cd brick-layering-script
   ```

2. **Place your G-code file**
   Ensure the G-code file is in the same directory as the script.

3. **Run the script**
   ```bash
   python main.py
   ```

4. **Check output**
   - The modified G-code will be saved as `edited.gcode` in the same directory.
   - The script also prints key settings and details (e.g., initial layer height, wall count) to the console.

---

## **How It Works**
- The script parses G-code files to extract configuration data from comments (e.g., `; initial_layer_print_height = ...`).
- It processes layers and walls, inserting commands to adjust Z-heights for staggered inner walls.
- Output G-code is saved to a new file for printing.

### Example Workflow
1. Slice a 3D model in Orca Slicer.
2. Export the G-code.
3. Run the script on the exported file.
4. Load the modified G-code into your 3D printer.

---

## **Issues**
### Known Bugs
- Staggering pattern doesn't work correctly when the number of wall loops is even.
  - The script currently struggles with "inner-outer-inner" sequences.
  - Wall order "inner-outer-inner" combined with an odd number of walls causes the bricking to be applied to the two outer-most inner walls.

### Reporting Issues
- Some slicer settings might break this script. Please report any errors or unexpected behavior:
  - Discord: `Divide#4615`
  - GitHub: Open an issue in this repository.

---

## **Contributing**
Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Commit your changes.
4. Open a pull request.

---

## **License**
This project is licensed under the **Creative Commons Attribution 4.0 International License (CC-BY 4.0)**. Feel free to use, share, and adapt the script with proper attribution.

---

## **Credits**
Created by me [Oskar Lindgren](https://github.com/OskarLindgren).

Special thanks to Orca Slicer and all contributers for the amazing slicer and the detailed G-code comments, which make post-processing like this possible.

---
