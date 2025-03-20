from address_parser import AddressStandardizer
import usaddress
from sentence_transformers import SentenceTransformer, util


model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")


def standarize_address(address):
    standardizer = AddressStandardizer()
    standardized_address = standardizer.standardize(address)
    return standardized_address


def compare_addresses(address1, address2, similarity_threshold=0.8):
    try:
        parsed1, _ = usaddress.tag(address1)
        parsed2, _ = usaddress.tag(address2)
    except usaddress.RepeatedLabelError as e:
        return f"Error parsing addresses: {e}"

    for parsed_address in [parsed1, parsed2]:
        place_name = parsed_address.get("PlaceName", "")
        if ", " in place_name:
            city, state_in_place = place_name.split(", ", 1)
            parsed_address["PlaceName"] = city
            parsed_address["StateName"] = (
                state_in_place
                if state_in_place != parsed_address.get("StateName", "")
                else parsed_address.get("StateName", "")
            )

    if parsed1.get("AddressNumber") != parsed2.get("AddressNumber"):
        return False
    if parsed1.get("ZipCode") != parsed2.get("ZipCode"):
        return False

    similarity_keys = [
        "StreetNamePreDirectional",
        "StreetName",
        "StreetNamePostType",
        "PlaceName",
        "StateName",
    ]
    for key in similarity_keys:
        value1 = parsed1.get(key, "").lower()
        value2 = parsed2.get(key, "").lower()

        if not value1 or not value2:
            continue

        # Compute similarity score
        embeddings1 = model.encode(value1, convert_to_tensor=True)
        embeddings2 = model.encode(value2, convert_to_tensor=True)
        similarity_score = util.cos_sim(embeddings1, embeddings2).item()

        if similarity_score < similarity_threshold:
            return False

    return True
