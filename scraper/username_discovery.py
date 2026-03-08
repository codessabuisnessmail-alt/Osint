class UsernameDiscoveryEngine:
    def __init__(self):
        pass
    
    def generate_usernames(self, first_name, last_name, birth_year=None):
        usernames = []
        first = first_name.lower().strip()
        last = last_name.lower().strip()
        
        usernames.extend([
            f"{first}{last}",
            f"{first}.{last}",
            f"{first}_{last}",
            f"{first[0]}{last}",
            f"{first}{last[0]}",
            f"{first[0]}{last[0]}"
        ])
        
        if birth_year:
            usernames.extend([
                f"{first}{last}{birth_year}",
                f"{first}{birth_year}",
                f"{first[0]}{last}{birth_year}"
            ])
        
        common_numbers = ['123', '01', '2023', '2024']
        for num in common_numbers:
            usernames.extend([
                f"{first}{last}{num}",
                f"{first}{num}",
                f"{first[0]}{last}{num}"
            ])
        
        usernames = list(set(usernames))
        usernames = [u for u in usernames if len(u) >= 3 and len(u) <= 30]
        
        return usernames
