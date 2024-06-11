# Installation
1. Install anaconda/miniconda and create an environment with python version 3.9.19, or run the command `conda create -n ENV_NAME python=3.9.19` replace 'ENV_NAME' which what you want to call your environment.
2. Load your environment using `conda activate ENV_NAME`
1. To install the required dependencies run `pip install -r requirements.txt`
2. Download the repo using `git clone https://github.com/bvsteja117/insightapp.git` 
3. Run the script using `python main.py`

# Usage

### Adding new people to the database
1. Go to the `Add/Modify` tab.
2. Type the name of the employee in the text box.
3. Click `Add New Entry` and make sure to have the employee in front of the camera.
4. Rotate face in a circle to cover all angles 
5. Click `Stop Recording` .

### Deleting Employees
1. Enter the name of the employee whose record is to be deleted in the `Delete` tab.
2. Click `Delete and Entry`

### Recognising People
1. Go to the `Face Recognition` tab and click `Start Recognition`.
2. Names of all the people in frame will be displayed on the screen with boxes around faces and names written on top of the boxes.

### Check In/Check Out
1. Go to the `Check In/Check Out` tab.
2. Click `Check-In` to check someone in.
3. Click `Check-out` to check someone out.
#### **NOTE: SOMEONE MUST BE CHECKED IN FIRST TO BE CHECKED OUT**

