import usaddress
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class AddressStandardizer:
    def __init__(self):
        self.us_state_abbreviations = [
            "AL",
            "AK",
            "AZ",
            "AR",
            "CA",
            "CO",
            "CT",
            "DE",
            "FL",
            "GA",
            "HI",
            "ID",
            "IL",
            "IN",
            "IA",
            "KS",
            "KY",
            "LA",
            "ME",
            "MD",
            "MA",
            "MI",
            "MN",
            "MS",
            "MO",
            "MT",
            "NE",
            "NV",
            "NH",
            "NJ",
            "NM",
            "NY",
            "NC",
            "ND",
            "OH",
            "OK",
            "OR",
            "PA",
            "RI",
            "SC",
            "SD",
            "TN",
            "TX",
            "UT",
            "VT",
            "VA",
            "WA",
            "WV",
            "WI",
            "WY",
        ]
        self.state_abbreviation_map = {
            "AL": "Alabama",
            "AK": "Alaska",
            "AZ": "Arizona",
            "AR": "Arkansas",
            "CA": "California",
            "CO": "Colorado",
            "CT": "Connecticut",
            "DE": "Delaware",
            "FL": "Florida",
            "GA": "Georgia",
            "HI": "Hawaii",
            "ID": "Idaho",
            "IL": "Illinois",
            "IN": "Indiana",
            "IA": "Iowa",
            "KS": "Kansas",
            "KY": "Kentucky",
            "LA": "Louisiana",
            "ME": "Maine",
            "MD": "Maryland",
            "MA": "Massachusetts",
            "MI": "Michigan",
            "MN": "Minnesota",
            "MS": "Mississippi",
            "MO": "Missouri",
            "MT": "Montana",
            "NE": "Nebraska",
            "NV": "Nevada",
            "NH": "New Hampshire",
            "NJ": "New Jersey",
            "NM": "New Mexico",
            "NY": "New York",
            "NC": "North Carolina",
            "ND": "North Dakota",
            "OH": "Ohio",
            "OK": "Oklahoma",
            "OR": "Oregon",
            "PA": "Pennsylvania",
            "RI": "Rhode Island",
            "SC": "South Carolina",
            "SD": "South Dakota",
            "TN": "Tennessee",
            "TX": "Texas",
            "UT": "Utah",
            "VT": "Vermont",
            "VA": "Virginia",
            "WA": "Washington",
            "WV": "West Virginia",
            "WI": "Wisconsin",
            "WY": "Wyoming",
        }

    def get_max_cosine_similarity(self, input_str, abbreviations):
        # Cosine similarity calculation
        vectorizer = CountVectorizer(analyzer="char")
        vectors = vectorizer.fit_transform([input_str] + abbreviations)
        cosine_similarities = cosine_similarity(vectors[0:1], vectors[1:]).flatten()
        max_index = cosine_similarities.argmax()
        return self.us_state_abbreviations[max_index]

    def is_valid_state(self, state):
        """
        Check if the given state is a valid US state.

        Args:
            state (str): The state to be validated.

        Returns:
            bool: True if the state is valid, False otherwise.
        """
        return state in self.us_state_abbreviations

    def extract_address_components(self, address):
        """Extracts the address components from the given address using usaddress

        Args:
            address (str): The address to be parsed.

        Returns:
            dict: A dictionary containing the address components.
        """
        return usaddress.tag(address)[0]

    def standardize_street_predirectional(self, street_name):
        """
        Standardizes the given street name using usaddress.

        Args:
            street_name (str): The street name to be standardized.

        Returns:
            str: The standardized street name.
        """
        street_map = {
                "n": "North",
                "s": "South",
                "e": "East",
                "w": "West"
        }
        if not street_name in ["west", "east", "north", "south"]: # streetname are normalized in lowercase 
            return street_map[street_name]

    def standardize_street_postype(self, street_name):
        """
        Standardizes the given street post type

        Args:
            street_name (str): The street name to be standardized.

        Returns:
            str: The standardized street name.
        """
        street_post_map = {
            "rd": "Road",
            "cres": "Crescent",
            "cv": "Cove",
            "dr": "Drive",
            "aly": "Alley",
            "st": "Street",
            "pkwy": "Parkway",
            "cir": "Circle",
            "blvd": "Boulevard",
            "cmp": "Compound",
            "pl": "Place",
            "ave": "Avenue",
            "ter": "Terrace",
            "cm": "Common",
            "hwy": "Highway",
            "ln": "Lane",
            "cmpd": "Compound",
            "sq": "Square",
            "ct": "Court",
        }
        if street_name in street_post_map.keys():
            return street_post_map[street_name]
        elif street_name in street_post_map.values():
            return street_name  # if the street name is already in the map then return the same street name

    # def standardize_place_name(self, place_name):
    #     """
    #     Standardizes the given place name

    #     Args:
    #         place_name (str): The place name to be standardized.

    #     Returns:
    #         str: The standardized place name.
    #     """
    #     place_map = {
    #         "Suite"
    #     }
    #     pass

    def standardize(self, address):
        """
        Standardize the given address using usaddress parsing.

        Args:
            address (str): The address to be standardized.

        Returns:
            str: The standardized address.
        """
        parsed_address = self.extract_address_components(address)
        AddressNumber = parsed_address.get("AddressNumber", "")
        StreetName = parsed_address.get("StreetName", "")
        StreetNamePreDirectional = parsed_address.get("StreetNamePreDirectional", "")
        if StreetNamePreDirectional:
            # Normalize the StreetPredirectional
            StreetNamePreDirectional = (
                StreetNamePreDirectional.lower().strip().replace(".", "")
            )
            StreetNamePreDirectional = self.standardize_street_predirectional(
                StreetNamePreDirectional
            )
        StreetNamePostType = parsed_address.get("StreetNamePostType", "")

        if StreetNamePostType:
            # Normalize the StreetNamePostType
            StreetNamePostType = StreetNamePostType.lower().strip().replace(".", "")

            StreetNamePostType = self.standardize_street_postype(StreetNamePostType)
        OccupancyType = parsed_address.get("OccupancyType", "")
        OccupancyIdentifier = parsed_address.get("OccupancyIdentifier", "")
        PlaceName = parsed_address.get("PlaceName", "")
        StateName = parsed_address.get("StateName", "")
        ZipCode = parsed_address.get("ZipCode", "")

        if self.is_valid_state(StateName):

            StateName = StateName
            # So the Statename can be also the full statename which is valid but is valid_statement will be false
        elif StateName in self.us_state_abbreviations:
            StateName = self.us_state_abbreviations[StateName]

        else:
            StateName = self.get_max_cosine_similarity(
                StateName, self.us_state_abbreviations
            )

        # Construct address
        street_address_parts = [
            AddressNumber,
            StreetNamePreDirectional,
            StreetName,
            StreetNamePostType,
        ]
        street_address = " ".join(part for part in street_address_parts if part)

        occupancy = (
            f"{OccupancyType} {OccupancyIdentifier}".strip()
            if OccupancyType or OccupancyIdentifier
            else ""
        )
        city_state_zip = ", ".join(
            part for part in [PlaceName, StateName, ZipCode] if part
        )

        # Final full address reconstruction
        full_address_parts = [street_address, occupancy, city_state_zip]
        full_address = ", ".join(part for part in full_address_parts if part)
        return full_address
