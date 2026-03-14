import json
from pathlib import Path


BRANDS = [
    "Sony",
    "Samsung",
    "Dell",
    "HP",
    "Logitech",
    "Razer",
    "Asus",
    "Lenovo",
    "Apple",
    "Bose",
]


BRAND_MULTIPLIERS = {
    "Sony": 1.08,
    "Samsung": 1.06,
    "Dell": 1.02,
    "HP": 0.99,
    "Logitech": 1.04,
    "Razer": 1.12,
    "Asus": 1.07,
    "Lenovo": 1.0,
    "Apple": 1.18,
    "Bose": 1.16,
}


CATALOG = [
    {
        "category": "Audio",
        "product_type": "Wireless Headphones",
        "search_terms": "wireless bluetooth headphones music calls immersive audio",
        "image_query": "wireless headphones audio technology",
        "base_price_inr": 12999,
    },
    {
        "category": "Audio",
        "product_type": "Noise Cancelling Earbuds",
        "search_terms": "noise cancelling earbuds commute travel calls compact audio",
        "image_query": "noise cancelling earbuds audio gadget",
        "base_price_inr": 8999,
    },
    {
        "category": "Audio",
        "product_type": "Bluetooth Speaker",
        "search_terms": "portable bluetooth speaker party outdoor sound home",
        "image_query": "bluetooth speaker portable audio",
        "base_price_inr": 7499,
    },
    {
        "category": "Gaming",
        "product_type": "Gaming Mouse",
        "search_terms": "gaming mouse esports precision rgb setup fps",
        "image_query": "gaming mouse rgb setup",
        "base_price_inr": 3999,
    },
    {
        "category": "Gaming",
        "product_type": "Mechanical Keyboard",
        "search_terms": "mechanical keyboard tactile gaming typing rgb",
        "image_query": "mechanical keyboard gaming desk",
        "base_price_inr": 6999,
    },
    {
        "category": "Gaming",
        "product_type": "Gaming Headset",
        "search_terms": "gaming headset voice chat surround sound multiplayer",
        "image_query": "gaming headset audio accessory",
        "base_price_inr": 7999,
    },
    {
        "category": "Gaming",
        "product_type": "Streaming Webcam",
        "search_terms": "streaming webcam creator live camera meetings",
        "image_query": "webcam streaming creator desk",
        "base_price_inr": 5999,
    },
    {
        "category": "Computers",
        "product_type": "Portable SSD",
        "search_terms": "portable ssd laptop storage backup creator fast transfer",
        "image_query": "portable ssd storage device",
        "base_price_inr": 8499,
    },
    {
        "category": "Computers",
        "product_type": "USB-C Hub",
        "search_terms": "usb c hub laptop hdmi expansion productivity",
        "image_query": "usb c hub laptop accessory",
        "base_price_inr": 3499,
    },
    {
        "category": "Computers",
        "product_type": "Laptop Stand",
        "search_terms": "laptop stand ergonomic desk office setup",
        "image_query": "laptop stand desk setup",
        "base_price_inr": 2499,
    },
    {
        "category": "Mobile",
        "product_type": "Wireless Charger",
        "search_terms": "wireless charger phone charging desk bedside qi",
        "image_query": "wireless charger smartphone desk",
        "base_price_inr": 2499,
    },
    {
        "category": "Mobile",
        "product_type": "Power Bank",
        "search_terms": "power bank fast charging travel battery backup",
        "image_query": "power bank charging gadget",
        "base_price_inr": 2999,
    },
    {
        "category": "Mobile",
        "product_type": "Phone Gimbal",
        "search_terms": "phone gimbal mobile videography creator stabilized video",
        "image_query": "phone gimbal videography gadget",
        "base_price_inr": 9999,
    },
    {
        "category": "Wearables",
        "product_type": "Smart Watch",
        "search_terms": "smart watch notifications fitness calls premium wearable",
        "image_query": "smart watch wearable tech",
        "base_price_inr": 17999,
    },
    {
        "category": "Wearables",
        "product_type": "Fitness Band",
        "search_terms": "fitness band steps workouts health tracking",
        "image_query": "fitness band wearable",
        "base_price_inr": 4999,
    },
    {
        "category": "Wearables",
        "product_type": "Smart Ring",
        "search_terms": "smart ring sleep recovery wellness wearable",
        "image_query": "smart ring wearable technology",
        "base_price_inr": 24999,
    },
    {
        "category": "Smart Home",
        "product_type": "Security Camera",
        "search_terms": "security camera home monitoring alerts wifi",
        "image_query": "security camera smart home",
        "base_price_inr": 6499,
    },
    {
        "category": "Smart Home",
        "product_type": "Smart Bulb",
        "search_terms": "smart bulb app lighting scenes home automation",
        "image_query": "smart bulb home lighting",
        "base_price_inr": 1999,
    },
    {
        "category": "Smart Home",
        "product_type": "Smart Plug",
        "search_terms": "smart plug remote control energy scheduling automation",
        "image_query": "smart plug home automation",
        "base_price_inr": 1799,
    },
    {
        "category": "Creator",
        "product_type": "Ring Light",
        "search_terms": "ring light creator video calls content studio",
        "image_query": "ring light creator desk",
        "base_price_inr": 2999,
    },
    {
        "category": "Creator",
        "product_type": "Tripod",
        "search_terms": "tripod camera phone creator stable shooting",
        "image_query": "tripod camera content creator",
        "base_price_inr": 2499,
    },
    {
        "category": "Office",
        "product_type": "Portable Monitor",
        "search_terms": "portable monitor laptop second screen productivity remote work",
        "image_query": "portable monitor workspace display",
        "base_price_inr": 14999,
    },
    {
        "category": "Office",
        "product_type": "Ergonomic Chair",
        "search_terms": "ergonomic chair laptop desk comfort office posture support",
        "image_query": "ergonomic office chair workspace",
        "base_price_inr": 12999,
    },
    {
        "category": "Accessories",
        "product_type": "Laptop Backpack",
        "search_terms": "laptop backpack commute travel student storage tech",
        "image_query": "laptop backpack travel accessory",
        "base_price_inr": 3999,
    },
    {
        "category": "Accessories",
        "product_type": "Tech Organizer",
        "search_terms": "tech organizer laptop cables chargers travel accessories pouch",
        "image_query": "tech organizer cables travel case",
        "base_price_inr": 1499,
    },
]


def build_description(brand: str, product_type: str, category: str, keywords: str) -> str:
    readable_keywords = keywords.replace(" ", ", ")
    return (
        f"{brand} {product_type} for modern {category.lower()} setups with "
        f"{readable_keywords}, premium everyday usability, and a polished design for students, creators, and professionals."
    )


def build_price(brand: str, base_price_inr: int) -> int:
    multiplier = BRAND_MULTIPLIERS.get(brand, 1.0)
    rounded_price = int(round((base_price_inr * multiplier) / 500.0) * 500)
    return max(rounded_price - 1, 999)


def main() -> None:
    products = []
    product_id = 1

    for item in CATALOG:
        for brand in BRANDS:
            products.append(
                {
                    "id": product_id,
                    "brand": brand,
                    "product_type": item["product_type"],
                    "name": f"{brand} {item['product_type']}",
                    "category": item["category"],
                    "description": build_description(
                        brand,
                        item["product_type"],
                        item["category"],
                        item["search_terms"],
                    ),
                    "search_terms": item["search_terms"],
                    "image_query": item["image_query"],
                    "price_inr": build_price(brand, item["base_price_inr"]),
                }
            )
            product_id += 1

    output_path = Path(__file__).with_name("products.json")
    output_path.write_text(json.dumps(products, indent=2), encoding="utf-8")

    print(f"{len(products)} products generated successfully")
    print(f"{len(CATALOG)} product varieties created across {len({item['category'] for item in CATALOG})} categories")


if __name__ == "__main__":
    main()
