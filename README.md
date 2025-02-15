# CulinaryMap

CulinaryMap is an application that displays dining locations based on proximity, with filters by tags and links to Google Maps for navigation. The database includes places that have been tested or recommended, ensuring a quality selection.

## Features
- Interactive map visualization of restaurants.
- Filters by cuisine type, location, and rating.
- Direct link to Google Maps for navigation.
- Option to mark places as visited and rate them with stars.
- Data stored in an encrypted JSON file for security and easy updates.

## Installation and Usage
### 1. Clone the repository
```sh
 git clone https://github.com/jviosca/CulinaryMap.git
```

### 2. Install dependencies
```sh
conda env create --prefix ./envs -f environment.yml
```

### 3. Run the application
```sh
streamlit run app.py
```

## Technologies Used
- **Python**: Main programming language.
- **Streamlit**: For the user interface.
- **Folium/Leaflet.js**: For map visualization.
- **Google Maps API**: For navigation.
- **SQLite / Encrypted JSON**: For data storage.

## Contributions
Contributions are welcome. If you wish to improve the application, fork the repository and submit a pull request.

## License
This project is licensed under the MIT License.
