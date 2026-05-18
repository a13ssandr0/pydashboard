_yml = """# Example configuration file for PyDashboard
#More documentation at https://a13ssandr0.github.io/pydashboard/config_file/

ansi_color: false
defaults:
  border: ["round", "cyan"]
  title_color: lightgreen
  refresh_interval: 5
grid:
  columns: [10, 15, 15, 10]
  rows: [9, 7, 3, 7, 5]
mods:
  clock:
    position:
      top: 0
      left: 1
      height: 1
      width: 2
  text:
    position:
      top: 1
      left: 0
      height: 2
      width: 4
    text: |-
        Thanks for installing PyDashboard, you are currently using an example configuration file located at:
        
        {CONFIG_FILE_PATH}
        
        Use your favourite text editor to edit the file, refer to 
        https://a13ssandr0.github.io/pydashboard/config_file/
        to know how to configure PyDashboard.
"""

def make_def_conf(file_path):
    return _yml.format(CONFIG_FILE_PATH=file_path)