"""Physical constants used across the simulator.

Values are for standard sea-level air at 15 °C. Bangkok is warmer (about 30 °C),
which lowers air density by about 5%; change these if you want to match the room
where the real rig will run.
"""

RHO = 1.225                 # air density, kg/m^3
SPEED_OF_SOUND = 340.3      # m/s
KINEMATIC_VISCOSITY = 1.46e-5  # m^2/s, used to report Reynolds numbers
INCH = 0.0254               # metres per inch
