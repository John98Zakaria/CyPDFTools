# CyPDF - A PDF Library that suits your basic needs
[![Documentation Status](https://readthedocs.org/projects/minipdfmerger/badge/?version=latest)](https://minipdfmerger.readthedocs.io/en/latest/?badge=latest)

CyPDF is a fully documented PDF library written in augmented Cython for your basic PDF needs.

---
## Features
* A progress bar showing you the current state of processing thanks to [tqdm](https://tqdm.github.io/)
* Deletion of pages
* Merging multiple PDF files into one cohesive file
* Rotate the entire document or single pages
* [TODO] Create PDF file from images



## Known Bugs
* Encrypted PDFs can't be processed
* PDFs with newline terminators other than "/n"
* Named destinations aren't handled properly



## Bug Reporting
Found a PDF that isn't properly functioning ?\
Here is how you make a bug report
1. Check the known bugs if it's not there continue
2. [Open an issue](https://github.com/John98Zakaria/CyPDFTools/issues)
2. Provide the code snippet that you used to cause the problem
3. If possible include the PDF itself into the report


## Contributing
If you're missing any features or want to suggest improvements
feel free to [open an issue](https://github.com/John98Zakaria/CyPDFTools/issues)