# Goal: Make the image morpher faster so larger images can be quickly morphed

# Plan:
* SPIKE on how others got morphing to be quick
    - compare their approach with mine, what's different about the workflows
    - pull down their code and step through to understand
* Write a unit test that asserts the correctness of the morph algorithm
    - this test will be used to quickly sanity check that the morph algorithm is still functional
    - Input (two small images, corresponding points, t=0.5) 
    - Output (assertEquals between just actual_img and expected_img)
* Add another unit test w/ logging such that after every morph, the image filenames and total morph time is recorded
