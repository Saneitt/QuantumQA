import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup


class HTMLSelectorExtractor:
    """Extracts selectors and semantic information from HTML documents."""
    
    def __init__(self):
        self.selectors = []
        self.semantic_map = {}
    
    def extract_selectors(self, html_content: str) -> Dict[str, Any]:
        """
        Extract all selectors (id, name, class, data-test) from HTML.
        Returns a dictionary with selectors organized by type and semantic meaning.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        selectors_data = {
            'all_selectors': [],
            'by_type': {
                'ids': [],
                'names': [],
                'classes': [],
                'data_test': []
            },
            'semantic': {
                'buttons': [],
                'inputs': [],
                'forms': [],
                'cart_elements': [],
                'payment_elements': [],
                'shipping_elements': [],
                'discount_elements': [],
                'validation_elements': []
            }
        }
        
        all_elements = soup.find_all()
        
        for element in all_elements:
            element_info = {
                'tag': element.name,
                'selectors': []
            }
            
            if element.get('id'):
                selector = f"#{element['id']}"
                selectors_data['by_type']['ids'].append(selector)
                selectors_data['all_selectors'].append(selector)
                element_info['selectors'].append(selector)
                element_info['id'] = element['id']
            
            if element.get('name'):
                selector = f"[name='{element['name']}']"
                selectors_data['by_type']['names'].append(selector)
                selectors_data['all_selectors'].append(selector)
                element_info['selectors'].append(selector)
                element_info['name'] = element['name']
            
            if element.get('class'):
                classes = element['class'] if isinstance(element['class'], list) else [element['class']]
                for cls in classes:
                    selector = f".{cls}"
                    selectors_data['by_type']['classes'].append(selector)
                    selectors_data['all_selectors'].append(selector)
                    element_info['selectors'].append(selector)
            
            if element.get('data-test'):
                selector = f"[data-test='{element['data-test']}']"
                selectors_data['by_type']['data_test'].append(selector)
                selectors_data['all_selectors'].append(selector)
                element_info['selectors'].append(selector)
            
            self._categorize_semantic(element, element_info, selectors_data)
        
        selectors_data['all_selectors'] = list(set(selectors_data['all_selectors']))
        
        return selectors_data
    
    def _categorize_semantic(self, element, element_info: Dict, selectors_data: Dict):
        """Categorize elements by semantic purpose."""
        text_content = element.get_text(strip=True).lower()
        element_id = element.get('id', '').lower()
        element_name = element.get('name', '').lower()
        element_class = ' '.join(element.get('class', [])).lower()
        
        if element.name == 'button' or element.get('type') == 'button' or element.get('type') == 'submit':
            selectors_data['semantic']['buttons'].append(element_info)
        
        if element.name == 'input' or element.name == 'textarea' or element.name == 'select':
            selectors_data['semantic']['inputs'].append(element_info)
        
        if element.name == 'form':
            selectors_data['semantic']['forms'].append(element_info)
        
        if any(keyword in text_content for keyword in ['cart', 'add to cart', 'quantity']):
            selectors_data['semantic']['cart_elements'].append(element_info)
        
        if any(keyword in element_id + element_name + element_class for keyword in ['cart', 'qty', 'quantity', 'total']):
            selectors_data['semantic']['cart_elements'].append(element_info)
        
        if any(keyword in text_content for keyword in ['payment', 'pay', 'credit', 'paypal']):
            selectors_data['semantic']['payment_elements'].append(element_info)
        
        if any(keyword in element_id + element_name + element_class for keyword in ['payment', 'pay']):
            selectors_data['semantic']['payment_elements'].append(element_info)
        
        if any(keyword in text_content for keyword in ['shipping', 'standard', 'express', 'delivery']):
            selectors_data['semantic']['shipping_elements'].append(element_info)
        
        if any(keyword in element_id + element_name + element_class for keyword in ['shipping', 'delivery']):
            selectors_data['semantic']['shipping_elements'].append(element_info)
        
        if any(keyword in text_content for keyword in ['discount', 'coupon', 'promo']):
            selectors_data['semantic']['discount_elements'].append(element_info)
        
        if any(keyword in element_id + element_name + element_class for keyword in ['discount', 'coupon', 'promo', 'code']):
            selectors_data['semantic']['discount_elements'].append(element_info)
        
        if any(keyword in element_class for keyword in ['error', 'invalid', 'validation']):
            selectors_data['semantic']['validation_elements'].append(element_info)
    
    def format_for_storage(self, selectors_data: Dict) -> str:
        """Format selectors data as a readable string for vector storage."""
        output = []
        
        output.append("=== HTML SELECTORS ===\n")
        output.append(f"Total unique selectors: {len(selectors_data['all_selectors'])}\n")
        
        output.append("\n--- Buttons ---")
        for btn in selectors_data['semantic']['buttons']:
            output.append(f"  {btn['tag']}: {', '.join(btn['selectors'])}")
        
        output.append("\n--- Input Fields ---")
        for inp in selectors_data['semantic']['inputs']:
            output.append(f"  {inp['tag']}: {', '.join(inp['selectors'])}")
        
        output.append("\n--- Cart Elements ---")
        for cart in selectors_data['semantic']['cart_elements']:
            output.append(f"  {cart['tag']}: {', '.join(cart['selectors'])}")
        
        output.append("\n--- Payment Elements ---")
        for pay in selectors_data['semantic']['payment_elements']:
            output.append(f"  {pay['tag']}: {', '.join(pay['selectors'])}")
        
        output.append("\n--- Shipping Elements ---")
        for ship in selectors_data['semantic']['shipping_elements']:
            output.append(f"  {ship['tag']}: {', '.join(ship['selectors'])}")
        
        output.append("\n--- Discount Elements ---")
        for disc in selectors_data['semantic']['discount_elements']:
            output.append(f"  {disc['tag']}: {', '.join(disc['selectors'])}")
        
        return '\n'.join(output)
