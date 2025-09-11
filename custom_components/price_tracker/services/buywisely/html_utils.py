from bs4 import BeautifulSoup
import bs4

def extract_image(soup):
    image_element = soup.select_one('div.MuiBox-root.mui-1ub93rr img')
    if image_element and 'src' in image_element.attrs:
        image = image_element['src']
        if image and isinstance(image, str) and image.startswith('/'):
            return 'https://buywisely.com.au' + image
        return image
    generic_img = soup.find('img')
    if generic_img and isinstance(generic_img, bs4.element.Tag):
        return generic_img.get('src')
    return None

def extract_title(soup):
    title_element = soup.select_one('h2')
    return title_element.text.strip() if title_element else None