# TASA_BSDF_tool
A simple GUI tool for converting BSDF data between Excel, LightTools, and ASAP formats.
Developed for internal use at TASA (Taiwan Space Agency) Optical Payload Division.

# How to Use

Launch `BSDF_tool.exe`.

The GUI provides two main functions:

---

## 1️⃣ Convert Excel → LightTools (.txt)
## Input Format Example
```Excel
列標籤	-180	-175	-170	-165	-160	...	180
0	2604.8				
5	2918.6	2933.1	3245	2972.6	3007.1
10	3462.7	3469.9	4057.2	3762.5	3485
15	3501.3	4109.8	3912	3916.7	4280.8
20	4472.1	4158.1	4250.5	4222.1	3771.8
...
90  ......
```
(Optional) Enable **排除異常值**
- Negative values will be set to 0
- Zero values will be interpolated from neighbors

## 2️⃣ Convert LightTools (Multiple AOI) → ASAP Scatter File
### Requirement
Place all LightTools `.txt` files into one folder.

File names must follow:

*_XXdeg.txt

Example:
```Folder
sample_0deg.txt
sample_30deg.txt
sample_60deg.txt
```
And:
- Select the folder containing all AOI files.
- Choose output filename.


## License

This repository is distributed under a custom license for internal use only.  
Please see the [LICENSE](./LICENSE) file for details.  
Unauthorized distribution or commercial use is prohibited.
