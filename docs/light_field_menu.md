# Light Field Menu

## Brainstorming figures

- Correctly project single-image points in space without feature matching
    - maximize observations
        - Taking the top left subimage and bottom right subimage
        - Take four images, one at each corner
    - What subaperature/main lens does the depth map correlate to?
    - How to sample from depth map with sub-picture?
    - where are the mla baseline captured? 
    - Where is the subimage?


- Look for [non-Lambertian surfaces](https://en.wikipedia.org/wiki/Lambertian_reflectance) by sweeping across the sub-images. 
    - Mask random reflections/refractions
    - Pick and use the "correct color/texture"


- Feature extraction just for deformation node
    - What does edge detection across depths look like?
    - Combining edges to a 3d edge map
    - How to pick key features? Can we use existing algorithms?




- how does mediapipe  limb / linear asumption
- tatum robotics limbs