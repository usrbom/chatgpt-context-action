from __future__ import annotations

import uuid

# Restaurant stubs — major US neighborhoods across multiple cities
RESTAURANTS = [
    # ── Chicago — River North ──────────────────────────────────
    {"venue_id": "VN_001", "venue_name": "Piccolo Sogno", "address": "464 N Milwaukee Ave, Chicago, IL", "cuisine": "Italian", "estimated_cost_per_person": 55, "rating": 4.7, "available_times": ["18:00", "18:30", "19:00", "19:30", "20:00"], "location_bucket": "River North"},
    {"venue_id": "VN_002", "venue_name": "RPM Italian", "address": "52 W Illinois St, Chicago, IL", "cuisine": "Italian", "estimated_cost_per_person": 65, "rating": 4.6, "available_times": ["17:30", "18:00", "19:00", "20:00", "20:30"], "location_bucket": "River North"},
    {"venue_id": "VN_003", "venue_name": "Bavette's Bar & Boeuf", "address": "218 W Kinzie St, Chicago, IL", "cuisine": "American", "estimated_cost_per_person": 70, "rating": 4.8, "available_times": ["18:00", "19:00", "20:00", "21:00"], "location_bucket": "River North"},
    {"venue_id": "VN_004", "venue_name": "GT Fish & Oyster", "address": "531 N Wells St, Chicago, IL", "cuisine": "Seafood", "estimated_cost_per_person": 60, "rating": 4.5, "available_times": ["17:00", "18:00", "19:00", "19:30", "20:00"], "location_bucket": "River North"},
    {"venue_id": "VN_005", "venue_name": "The Purple Pig", "address": "500 N Michigan Ave, Chicago, IL", "cuisine": "Mediterranean", "estimated_cost_per_person": 45, "rating": 4.6, "available_times": ["17:00", "18:00", "19:00", "22:00", "22:30"], "location_bucket": "River North"},
    {"venue_id": "VN_006", "venue_name": "Nico Osteria", "address": "1015 N Rush St, Chicago, IL", "cuisine": "Italian", "estimated_cost_per_person": 75, "rating": 4.4, "available_times": ["18:00", "19:00", "20:00"], "location_bucket": "River North"},
    # ── Chicago — Riverfront ───────────────────────────────────
    {"venue_id": "VN_007", "venue_name": "Chicago Riverwalk Café", "address": "180 N Michigan Ave, Chicago, IL", "cuisine": "American", "estimated_cost_per_person": 30, "rating": 4.2, "available_times": ["11:00", "12:00", "13:00", "14:00", "15:00"], "location_bucket": "Riverfront"},
    {"venue_id": "VN_008", "venue_name": "BOKA", "address": "1729 N Halsted St, Chicago, IL", "cuisine": "New American", "estimated_cost_per_person": 80, "rating": 4.7, "available_times": ["12:00", "12:30", "13:00", "13:30"], "location_bucket": "Riverfront"},
    {"venue_id": "VN_009", "venue_name": "Beatrix", "address": "519 N Clark St, Chicago, IL", "cuisine": "American", "estimated_cost_per_person": 35, "rating": 4.3, "available_times": ["11:00", "12:00", "13:00", "14:00"], "location_bucket": "Riverfront"},
    # ── Chicago — Lincoln Park ─────────────────────────────────
    {"venue_id": "VN_010", "venue_name": "Batter & Berries", "address": "2748 N Lincoln Ave, Chicago, IL", "cuisine": "American", "estimated_cost_per_person": 20, "rating": 4.6, "available_times": ["08:00", "09:00", "10:00", "11:00"], "location_bucket": "Lincoln Park"},
    {"venue_id": "VN_011", "venue_name": "North Pond", "address": "2610 N Cannon Dr, Chicago, IL", "cuisine": "American", "estimated_cost_per_person": 90, "rating": 4.5, "available_times": ["11:30", "12:00", "18:00", "19:00", "20:00"], "location_bucket": "Lincoln Park"},
    # ── Chicago — Wicker Park ──────────────────────────────────
    {"venue_id": "VN_012", "venue_name": "Jam", "address": "3057 W Logan Blvd, Chicago, IL", "cuisine": "American", "estimated_cost_per_person": 18, "rating": 4.5, "available_times": ["08:00", "09:00", "10:00", "11:00"], "location_bucket": "Wicker Park"},
    {"venue_id": "VN_013", "venue_name": "Dove's Luncheonette", "address": "1545 N Damen Ave, Chicago, IL", "cuisine": "Mexican", "estimated_cost_per_person": 22, "rating": 4.6, "available_times": ["09:00", "10:00", "11:00"], "location_bucket": "Wicker Park"},
    {"venue_id": "VN_014", "venue_name": "Big Star", "address": "1531 N Damen Ave, Chicago, IL", "cuisine": "Mexican", "estimated_cost_per_person": 20, "rating": 4.4, "available_times": ["11:00", "12:00", "17:00", "18:00", "22:00"], "location_bucket": "Wicker Park"},
    # ── Chicago — Loop ─────────────────────────────────────────
    {"venue_id": "VN_015", "venue_name": "The Gage", "address": "24 S Michigan Ave, Chicago, IL", "cuisine": "American", "estimated_cost_per_person": 45, "rating": 4.4, "available_times": ["11:30", "12:00", "12:30", "13:00", "13:30"], "location_bucket": "Loop"},
    {"venue_id": "VN_016", "venue_name": "Cindy's", "address": "12 S Michigan Ave, Chicago, IL", "cuisine": "American", "estimated_cost_per_person": 55, "rating": 4.5, "available_times": ["11:30", "12:00", "13:00", "17:30", "18:00"], "location_bucket": "Loop"},
    # ── Chicago — West Loop ────────────────────────────────────
    {"venue_id": "VN_017", "venue_name": "Au Cheval", "address": "800 W Randolph St, Chicago, IL", "cuisine": "American", "estimated_cost_per_person": 30, "rating": 4.7, "available_times": ["22:00", "22:30", "23:00"], "location_bucket": "West Loop"},
    {"venue_id": "VN_018", "venue_name": "Girl & the Goat", "address": "809 W Randolph St, Chicago, IL", "cuisine": "American", "estimated_cost_per_person": 65, "rating": 4.6, "available_times": ["17:30", "18:00", "18:30", "19:00", "20:00"], "location_bucket": "West Loop"},
    # ── Los Angeles — Westwood ─────────────────────────────────
    {"venue_id": "VN_019", "venue_name": "Napa Valley Grille", "address": "1100 Glendon Ave, Los Angeles, CA", "cuisine": "American", "estimated_cost_per_person": 55, "rating": 4.3, "available_times": ["11:30", "12:00", "13:00", "18:00", "19:00"], "location_bucket": "Westwood"},
    {"venue_id": "VN_020", "venue_name": "Tanino Ristorante", "address": "1043 Westwood Blvd, Los Angeles, CA", "cuisine": "Italian", "estimated_cost_per_person": 60, "rating": 4.5, "available_times": ["12:00", "18:00", "18:30", "19:00", "20:00"], "location_bucket": "Westwood"},
    {"venue_id": "VN_021", "venue_name": "Lamonica's NY Pizza", "address": "1066 Gayley Ave, Los Angeles, CA", "cuisine": "Italian", "estimated_cost_per_person": 18, "rating": 4.4, "available_times": ["11:00", "12:00", "13:00", "17:00", "18:00", "19:00"], "location_bucket": "Westwood"},
    {"venue_id": "VN_022", "venue_name": "Siam BBQ", "address": "10968 Le Conte Ave, Los Angeles, CA", "cuisine": "Asian", "estimated_cost_per_person": 20, "rating": 4.2, "available_times": ["11:30", "12:00", "17:30", "18:00", "19:00"], "location_bucket": "Westwood"},
    {"venue_id": "VN_023", "venue_name": "In-N-Out Burger Westwood", "address": "922 Gayley Ave, Los Angeles, CA", "cuisine": "American", "estimated_cost_per_person": 10, "rating": 4.6, "available_times": ["10:30", "11:00", "12:00", "13:00", "17:00", "18:00", "20:00", "22:00"], "location_bucket": "Westwood"},
    {"venue_id": "VN_024", "venue_name": "Diddy Riese", "address": "926 Broxton Ave, Los Angeles, CA", "cuisine": "American", "estimated_cost_per_person": 5, "rating": 4.7, "available_times": ["11:00", "12:00", "14:00", "16:00", "18:00", "20:00"], "location_bucket": "Westwood"},
    # ── Los Angeles — Santa Monica ─────────────────────────────
    {"venue_id": "VN_025", "venue_name": "Rustic Canyon", "address": "1119 Wilshire Blvd, Santa Monica, CA", "cuisine": "American", "estimated_cost_per_person": 70, "rating": 4.7, "available_times": ["17:30", "18:00", "19:00", "20:00"], "location_bucket": "Santa Monica"},
    {"venue_id": "VN_026", "venue_name": "Huckleberry Café", "address": "1014 Wilshire Blvd, Santa Monica, CA", "cuisine": "American", "estimated_cost_per_person": 25, "rating": 4.6, "available_times": ["08:00", "09:00", "10:00", "11:00", "12:00"], "location_bucket": "Santa Monica"},
    {"venue_id": "VN_027", "venue_name": "Mélisse", "address": "1104 Wilshire Blvd, Santa Monica, CA", "cuisine": "French", "estimated_cost_per_person": 120, "rating": 4.8, "available_times": ["18:00", "18:30", "19:00", "20:00"], "location_bucket": "Santa Monica"},
    {"venue_id": "VN_028", "venue_name": "Tar & Roses", "address": "602 Santa Monica Blvd, Santa Monica, CA", "cuisine": "American", "estimated_cost_per_person": 50, "rating": 4.5, "available_times": ["17:30", "18:00", "19:00", "20:00", "22:00"], "location_bucket": "Santa Monica"},
    # ── Los Angeles — Beverly Hills ────────────────────────────
    {"venue_id": "VN_029", "venue_name": "Spago Beverly Hills", "address": "176 N Canon Dr, Beverly Hills, CA", "cuisine": "American", "estimated_cost_per_person": 110, "rating": 4.6, "available_times": ["12:00", "13:00", "18:00", "19:00", "20:00"], "location_bucket": "Beverly Hills"},
    {"venue_id": "VN_030", "venue_name": "il Cielo", "address": "9018 Burton Way, Beverly Hills, CA", "cuisine": "Italian", "estimated_cost_per_person": 85, "rating": 4.5, "available_times": ["12:00", "18:00", "18:30", "19:00", "20:00"], "location_bucket": "Beverly Hills"},
    {"venue_id": "VN_031", "venue_name": "Matsuhisa", "address": "129 N La Cienega Blvd, Beverly Hills, CA", "cuisine": "Japanese", "estimated_cost_per_person": 95, "rating": 4.7, "available_times": ["18:00", "18:30", "19:00", "20:00"], "location_bucket": "Beverly Hills"},
    # ── Los Angeles — West Hollywood ───────────────────────────
    {"venue_id": "VN_032", "venue_name": "Craig's", "address": "8826 Melrose Ave, West Hollywood, CA", "cuisine": "American", "estimated_cost_per_person": 65, "rating": 4.4, "available_times": ["12:00", "18:00", "19:00", "20:00", "22:00"], "location_bucket": "West Hollywood"},
    {"venue_id": "VN_033", "venue_name": "Nobu West Hollywood", "address": "8764 Melrose Ave, West Hollywood, CA", "cuisine": "Japanese", "estimated_cost_per_person": 90, "rating": 4.6, "available_times": ["18:00", "18:30", "19:00", "20:00"], "location_bucket": "West Hollywood"},
    {"venue_id": "VN_034", "venue_name": "Sur Restaurant", "address": "606 N Robertson Blvd, West Hollywood, CA", "cuisine": "American", "estimated_cost_per_person": 55, "rating": 4.3, "available_times": ["17:30", "18:00", "19:00", "20:00"], "location_bucket": "West Hollywood"},
    # ── Los Angeles — Venice Beach ────────────────────────────
    {"venue_id": "VN_070", "venue_name": "Gjelina", "address": "1429 Abbot Kinney Blvd, Venice, CA", "cuisine": "American", "estimated_cost_per_person": 55, "rating": 4.6, "available_times": ["11:00", "12:00", "18:00", "19:00", "20:00", "22:00"], "location_bucket": "Venice Beach"},
    {"venue_id": "VN_071", "venue_name": "Gjusta", "address": "320 Sunset Ave, Venice, CA", "cuisine": "American", "estimated_cost_per_person": 25, "rating": 4.7, "available_times": ["07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "13:00"], "location_bucket": "Venice Beach"},
    {"venue_id": "VN_072", "venue_name": "Felix Trattoria", "address": "1023 Abbot Kinney Blvd, Venice, CA", "cuisine": "Italian", "estimated_cost_per_person": 65, "rating": 4.7, "available_times": ["17:30", "18:00", "19:00", "20:00"], "location_bucket": "Venice Beach"},
    {"venue_id": "VN_073", "venue_name": "Gget", "address": "1260 Abbot Kinney Blvd, Venice, CA", "cuisine": "American", "estimated_cost_per_person": 20, "rating": 4.4, "available_times": ["08:00", "09:00", "10:00", "11:00", "12:00", "13:00"], "location_bucket": "Venice Beach"},
    {"venue_id": "VN_074", "venue_name": "Superba Food + Bread", "address": "1900 S Lincoln Blvd, Venice, CA", "cuisine": "American", "estimated_cost_per_person": 22, "rating": 4.3, "available_times": ["08:00", "09:00", "10:00", "11:00", "12:00"], "location_bucket": "Venice Beach"},
    # ── Los Angeles — Silver Lake ──────────────────────────────
    {"venue_id": "VN_035", "venue_name": "Alimento", "address": "1710 Silver Lake Blvd, Los Angeles, CA", "cuisine": "Italian", "estimated_cost_per_person": 55, "rating": 4.6, "available_times": ["18:00", "18:30", "19:00", "20:00"], "location_bucket": "Silver Lake"},
    {"venue_id": "VN_036", "venue_name": "Sqirl", "address": "720 N Virgil Ave, Los Angeles, CA", "cuisine": "American", "estimated_cost_per_person": 20, "rating": 4.5, "available_times": ["08:00", "09:00", "10:00", "11:00", "12:00", "13:00"], "location_bucket": "Silver Lake"},
    # ── Los Angeles — Downtown LA ──────────────────────────────
    {"venue_id": "VN_037", "venue_name": "Bestia", "address": "2121 E 7th Pl, Los Angeles, CA", "cuisine": "Italian", "estimated_cost_per_person": 70, "rating": 4.7, "available_times": ["18:00", "18:30", "19:00", "20:00", "22:00"], "location_bucket": "Downtown LA"},
    {"venue_id": "VN_038", "venue_name": "Bavel", "address": "500 Mateo St, Los Angeles, CA", "cuisine": "Mediterranean", "estimated_cost_per_person": 65, "rating": 4.7, "available_times": ["17:30", "18:00", "19:00", "20:00"], "location_bucket": "Downtown LA"},
    {"venue_id": "VN_039", "venue_name": "Perch", "address": "448 S Hill St, Los Angeles, CA", "cuisine": "French", "estimated_cost_per_person": 60, "rating": 4.4, "available_times": ["11:00", "12:00", "17:30", "18:00", "19:00", "22:00"], "location_bucket": "Downtown LA"},
    # ── New York — Midtown ─────────────────────────────────────
    {"venue_id": "VN_040", "venue_name": "Le Bernardin", "address": "155 W 51st St, New York, NY", "cuisine": "Seafood", "estimated_cost_per_person": 185, "rating": 4.9, "available_times": ["12:00", "13:00", "18:00", "19:00", "20:00"], "location_bucket": "Midtown"},
    {"venue_id": "VN_041", "venue_name": "The Modern", "address": "9 W 53rd St, New York, NY", "cuisine": "American", "estimated_cost_per_person": 120, "rating": 4.7, "available_times": ["12:00", "18:30", "19:00", "20:00"], "location_bucket": "Midtown"},
    {"venue_id": "VN_042", "venue_name": "Carmine's Midtown", "address": "200 W 44th St, New York, NY", "cuisine": "Italian", "estimated_cost_per_person": 40, "rating": 4.4, "available_times": ["11:30", "12:00", "17:00", "18:00", "19:00", "20:00"], "location_bucket": "Midtown"},
    # ── New York — West Village ────────────────────────────────
    {"venue_id": "VN_043", "venue_name": "Buvette", "address": "42 Grove St, New York, NY", "cuisine": "French", "estimated_cost_per_person": 45, "rating": 4.6, "available_times": ["09:00", "10:00", "11:00", "12:00", "18:00", "19:00"], "location_bucket": "West Village"},
    {"venue_id": "VN_044", "venue_name": "Via Carota", "address": "51 Grove St, New York, NY", "cuisine": "Italian", "estimated_cost_per_person": 55, "rating": 4.7, "available_times": ["11:30", "12:00", "18:00", "19:00", "20:00"], "location_bucket": "West Village"},
    {"venue_id": "VN_045", "venue_name": "Babbo", "address": "110 Waverly Pl, New York, NY", "cuisine": "Italian", "estimated_cost_per_person": 80, "rating": 4.6, "available_times": ["17:30", "18:00", "19:00", "20:00"], "location_bucket": "West Village"},
    # ── New York — SoHo ───────────────────────────────────────
    {"venue_id": "VN_046", "venue_name": "Balthazar", "address": "80 Spring St, New York, NY", "cuisine": "French", "estimated_cost_per_person": 70, "rating": 4.5, "available_times": ["08:00", "11:30", "12:00", "18:00", "19:00", "22:00"], "location_bucket": "SoHo"},
    {"venue_id": "VN_047", "venue_name": "Lure Fishbar", "address": "142 Mercer St, New York, NY", "cuisine": "Seafood", "estimated_cost_per_person": 65, "rating": 4.4, "available_times": ["12:00", "18:00", "19:00", "20:00"], "location_bucket": "SoHo"},
    # ── New York — Brooklyn ────────────────────────────────────
    {"venue_id": "VN_048", "venue_name": "Peter Luger Steak House", "address": "178 Broadway, Brooklyn, NY", "cuisine": "American", "estimated_cost_per_person": 100, "rating": 4.6, "available_times": ["12:00", "13:00", "17:30", "18:00", "19:00", "20:00"], "location_bucket": "Brooklyn"},
    {"venue_id": "VN_049", "venue_name": "Juliana's Pizza", "address": "19 Old Fulton St, Brooklyn, NY", "cuisine": "Italian", "estimated_cost_per_person": 25, "rating": 4.7, "available_times": ["11:30", "12:00", "13:00", "17:00", "18:00", "19:00"], "location_bucket": "Brooklyn"},
    # ── San Francisco — Mission ────────────────────────────────
    {"venue_id": "VN_050", "venue_name": "Flour + Water", "address": "2401 Harrison St, San Francisco, CA", "cuisine": "Italian", "estimated_cost_per_person": 60, "rating": 4.6, "available_times": ["17:30", "18:00", "19:00", "20:00"], "location_bucket": "Mission"},
    {"venue_id": "VN_051", "venue_name": "Tartine Manufactory", "address": "595 Alabama St, San Francisco, CA", "cuisine": "American", "estimated_cost_per_person": 30, "rating": 4.7, "available_times": ["08:00", "09:00", "10:00", "11:00", "12:00", "17:00", "18:00"], "location_bucket": "Mission"},
    {"venue_id": "VN_052", "venue_name": "La Taqueria", "address": "2889 Mission St, San Francisco, CA", "cuisine": "Mexican", "estimated_cost_per_person": 15, "rating": 4.5, "available_times": ["11:00", "12:00", "13:00", "14:00", "17:00", "18:00"], "location_bucket": "Mission"},
    # ── San Francisco — North Beach ────────────────────────────
    {"venue_id": "VN_053", "venue_name": "Cotogna", "address": "490 Pacific Ave, San Francisco, CA", "cuisine": "Italian", "estimated_cost_per_person": 70, "rating": 4.7, "available_times": ["11:30", "12:00", "17:30", "18:00", "19:00"], "location_bucket": "North Beach"},
    {"venue_id": "VN_054", "venue_name": "Vesuvio Café", "address": "255 Columbus Ave, San Francisco, CA", "cuisine": "American", "estimated_cost_per_person": 20, "rating": 4.3, "available_times": ["10:00", "12:00", "14:00", "17:00", "20:00", "22:00"], "location_bucket": "North Beach"},
    # ── San Francisco — Hayes Valley ───────────────────────────
    {"venue_id": "VN_055", "venue_name": "Rich Table", "address": "199 Gough St, San Francisco, CA", "cuisine": "American", "estimated_cost_per_person": 75, "rating": 4.7, "available_times": ["17:30", "18:00", "19:00", "20:00"], "location_bucket": "Hayes Valley"},
    {"venue_id": "VN_056", "venue_name": "Monsieur Benjamin", "address": "451 Gough St, San Francisco, CA", "cuisine": "French", "estimated_cost_per_person": 65, "rating": 4.5, "available_times": ["11:30", "12:00", "17:30", "18:00", "19:00"], "location_bucket": "Hayes Valley"},
    # ── Miami — South Beach ────────────────────────────────────
    {"venue_id": "VN_057", "venue_name": "Joe's Stone Crab", "address": "11 Washington Ave, Miami Beach, FL", "cuisine": "Seafood", "estimated_cost_per_person": 90, "rating": 4.6, "available_times": ["12:00", "13:00", "17:30", "18:00", "19:00", "20:00"], "location_bucket": "South Beach"},
    {"venue_id": "VN_058", "venue_name": "Yardbird Southern Table", "address": "1600 Lenox Ave, Miami Beach, FL", "cuisine": "American", "estimated_cost_per_person": 55, "rating": 4.5, "available_times": ["10:00", "11:00", "12:00", "18:00", "19:00", "20:00"], "location_bucket": "South Beach"},
    # ── Miami — Wynwood ────────────────────────────────────────
    {"venue_id": "VN_059", "venue_name": "KYU Miami", "address": "251 NW 25th St, Miami, FL", "cuisine": "Asian", "estimated_cost_per_person": 60, "rating": 4.7, "available_times": ["12:00", "13:00", "18:00", "19:00", "20:00"], "location_bucket": "Wynwood"},
    {"venue_id": "VN_060", "venue_name": "Kyu Wynwood", "address": "186 NW 29th St, Miami, FL", "cuisine": "American", "estimated_cost_per_person": 45, "rating": 4.4, "available_times": ["11:00", "12:00", "18:00", "19:00"], "location_bucket": "Wynwood"},
    # ── Washington DC — Georgetown ─────────────────────────────
    {"venue_id": "VN_061", "venue_name": "1789 Restaurant", "address": "1226 36th St NW, Washington, DC", "cuisine": "American", "estimated_cost_per_person": 80, "rating": 4.6, "available_times": ["17:30", "18:00", "19:00", "20:00"], "location_bucket": "Georgetown"},
    {"venue_id": "VN_062", "venue_name": "Fiola Mare", "address": "3050 K St NW, Washington, DC", "cuisine": "Seafood", "estimated_cost_per_person": 95, "rating": 4.7, "available_times": ["12:00", "18:00", "18:30", "19:00", "20:00"], "location_bucket": "Georgetown"},
    # ── Boston — Back Bay ──────────────────────────────────────
    {"venue_id": "VN_063", "venue_name": "Sorellina", "address": "1 Huntington Ave, Boston, MA", "cuisine": "Italian", "estimated_cost_per_person": 85, "rating": 4.6, "available_times": ["17:30", "18:00", "19:00", "20:00"], "location_bucket": "Back Bay"},
    {"venue_id": "VN_064", "venue_name": "Saltie Girl", "address": "279 Dartmouth St, Boston, MA", "cuisine": "Seafood", "estimated_cost_per_person": 75, "rating": 4.7, "available_times": ["17:00", "17:30", "18:00", "19:00", "20:00"], "location_bucket": "Back Bay"},
    # ── Seattle — Capitol Hill ─────────────────────────────────
    {"venue_id": "VN_065", "venue_name": "Canlis", "address": "2576 Aurora Ave N, Seattle, WA", "cuisine": "American", "estimated_cost_per_person": 120, "rating": 4.8, "available_times": ["17:30", "18:00", "19:00", "20:00"], "location_bucket": "Capitol Hill"},
    {"venue_id": "VN_066", "venue_name": "Altura", "address": "617 Broadway E, Seattle, WA", "cuisine": "Italian", "estimated_cost_per_person": 80, "rating": 4.6, "available_times": ["17:30", "18:00", "19:00", "20:00"], "location_bucket": "Capitol Hill"},
    # ── Austin — East Austin ───────────────────────────────────
    {"venue_id": "VN_067", "venue_name": "Loro Asian Smokehouse", "address": "2115 S Lamar Blvd, Austin, TX", "cuisine": "Asian", "estimated_cost_per_person": 35, "rating": 4.5, "available_times": ["11:00", "12:00", "17:00", "18:00", "19:00", "20:00"], "location_bucket": "East Austin"},
    {"venue_id": "VN_068", "venue_name": "Franklin Barbecue", "address": "900 E 11th St, Austin, TX", "cuisine": "American", "estimated_cost_per_person": 25, "rating": 4.8, "available_times": ["11:00", "12:00", "13:00"], "location_bucket": "East Austin"},
]

# Build a lookup index keyed by normalized location name
_LOCATION_INDEX: dict[str, list[dict]] = {}
for _r in RESTAURANTS:
    _key = _r["location_bucket"].lower()
    _LOCATION_INDEX.setdefault(_key, []).append(_r)


def search_restaurants(location: str, date: str, time: str, party_size: int, cuisine: str | None) -> list[dict]:
    location_key = location.strip().lower()
    candidates = _LOCATION_INDEX.get(location_key, [])

    # Fuzzy fallback: partial match on location name
    if not candidates:
        for key, venues in _LOCATION_INDEX.items():
            if location_key in key or key in location_key:
                candidates = venues
                break

    if cuisine:
        cuisine_lower = cuisine.lower()
        filtered = [r for r in candidates if r["cuisine"].lower() == cuisine_lower]
        candidates = filtered if filtered else candidates  # fall back to all if no cuisine match

    # Sort by rating descending (agent re-ranks by history)
    return sorted(candidates, key=lambda x: -x["rating"])


def book_restaurant(
    venue_id: str,
    venue_name: str,
    date: str,
    time: str,
    party_size: int,
    counterparty_name: str,
    counterparty_phone: str,
) -> dict:
    confirmation_id = "CONF-" + str(uuid.uuid4())[:8].upper()
    return {
        "booking_confirmed": True,
        "confirmation_id": confirmation_id,
        "venue_name": venue_name,
        "date": date,
        "time": time,
        "party_size": party_size,
        "error_message": None,
    }


def get_venue_by_id(venue_id: str) -> dict | None:
    for r in RESTAURANTS:
        if r["venue_id"] == venue_id:
            return r
    return None
