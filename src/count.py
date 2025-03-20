import re


def normalize_address_for_count(address):
    address = re.sub(r"[.,]", "", address)
    address = address.lower().strip()
    return address


def find_rent_missing(lease_addresses, rent_addresses):

    lease_addresses = set(lease_addresses)
    rent_addresses = set(rent_addresses)
    print("----------------------------------")
    print("LEASE ADDRESS")
    print(lease_addresses)
    print("RENT ADDRESS")
    print(rent_addresses)
    print("---------------------------------")
    normalized_lease = {
        normalize_address_for_count(addr): addr for addr in lease_addresses
    }
    normalized_rent = {
        normalize_address_for_count(addr): addr for addr in rent_addresses
    }
    rent_missing_address = [
        address
        for address in lease_addresses
        if normalize_address_for_count(address) not in normalized_rent
    ]
    return set(rent_missing_address), len(rent_missing_address)


# def find_lease_missing(lease_addresses, rent_addresses):
#     normalized_lease = {normalize_address_for_count(addr): addr for addr in lease_addresses}
#     normalized_rent = {normalize_address_for_count(addr): addr for addr in rent_addresses}
#     lease_missing_address = [
#         address for address in rent_addresses
#         if normalize_address_for_count(address) not in normalized_lease
#     ]
#     return set(lease_missing_address), len(lease_missing_address)


def find_lease_missing(unmatched_leases, unmatched_rentrolls):
    lease_units = {lease["unit_number"].strip().lower() for lease in unmatched_leases}

    missing_addresses_with_units = []
    missing_counts = []

    for rentroll in unmatched_rentrolls:
        address = rentroll["property_address"].strip()
        units = [unit.strip().lower() for unit in rentroll["unit_numbers"]]

        missing_units = [unit for unit in units if unit not in lease_units]
        if missing_units:
            for unit in missing_units:
                formatted_address = f"{address}, units {unit}"
                missing_addresses_with_units.append(formatted_address)
            missing_counts.append(len(missing_units))
    total_lease_missing = sum(missing_counts)
    return missing_addresses_with_units, missing_counts, total_lease_missing


def find_lease_missing_by_address(unmatched_leases, unmatched_rentrolls):
    lease_units_by_address = {}
    for lease in unmatched_leases:
        address = lease["lease_property_address"].strip().lower()
        unit = lease["unit_number"].strip().lower()

        if address not in lease_units_by_address:
            lease_units_by_address[address] = set()
        lease_units_by_address[address].add(unit)

    missing_addresses_with_units = []
    missing_counts = []

    for rentroll in unmatched_rentrolls:
        address = rentroll["property_address"].strip().lower()
        units_in_rentroll = set(
            unit.strip().lower() for unit in rentroll["unit_numbers"]
        )

        if address in lease_units_by_address:
            lease_units = lease_units_by_address[address]
            missing_units = units_in_rentroll - lease_units

            if missing_units:
                for unit in missing_units:
                    formatted_address = f"{address}, unit {unit}"
                    missing_addresses_with_units.append(formatted_address)
                missing_counts.append(len(missing_units))

    total_missing_units = sum(missing_counts)

    return missing_addresses_with_units, missing_counts, total_missing_units
