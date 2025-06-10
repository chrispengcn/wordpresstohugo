
# WordPress to Hugo Exporter Pro  

Export WordPress posts, pages, and products into Hugo-compatible Markdown files, supporting **Page Bundle structure** and **multi-format images (WebP)**. Perfectly adapts to Hugo's image processing rules.  


## 🌟 Core Features  

### 1. **Hugo Page Bundle Structure**  
- Exports content in the standard Hugo Page Bundle format:  
  ```  
  content/  
  └── {type}/          # post/pages/products  
      └── {slug}/      # Post/page/product slug  
          ├── index.md  # Markdown content  
          └── {image files} # Images saved directly (e.g., .jpg.webp)  
  ```  
- Automatically generates `index.md` with YAML front matter and content.  

### 2. **Multi-Format Image Support**  
- Extracts all images from WordPress content (including featured images), downloads them, and saves them in `.jpg.webp`, `.png.webp` formats.  
- Automatically replaces image URLs in Markdown with Hugo shortcodes:  
  ```markdown  
  {{< img src="image.jpg" alt="Image description" >}}  
  ```  
  Hugo will automatically recognize the `.webp` file in the same directory and prioritize loading the WebP format.  

### 3. **Complete Metadata Migration**  
- Supports migrating the following information:  
  - Title, Slug, publication date  
  - Categories, tags  
  - Featured images, in-content images  
  - WooCommerce product data (SKU, price, description, etc.)  
- Generates standard Hugo YAML Front Matter:  
  ```yaml  
  ---  
  layout: post  
  title: "Post Title"  
  slug: "my-post"  
  date: "2023-10-01 12:00:00"  
  categories:  
    - Technology  
  tags:  
    - Hugo  
    - WordPress  
  featuredImage: "featured.jpg.webp"  
  ---  
  ```  

### 4. **Flexible Content Type Support**  
- Exports posts, pages, and WooCommerce products.  
- Filter by content type or export all types at once.  


## 🚀 Usage Guide  

### 1. Install the Plugin  
- Download the plugin file or upload it via WordPress Admin → Plugins → Add New.  
- After activation, navigate to Dashboard → Hugo Export.  

### 2. Configure Export Settings  
- **Base Export Directory**: Set the root directory of your Hugo project (e.g., `/var/www/hugo/`).  
- **Content Type**: Select the content type to export (posts/pages/products/all).  
- **Include Category Directories** (optional): Generate multi-level directories by category (e.g., `posts/categories/technology/my-post/`).  

### 3. Start Exporting  
- Click "Start Export." The plugin will process content and display progress logs.  
- After completion, the directory structure will be:  
  ```  
  hugo/  
  ├── content/  
  │   ├── posts/  
  │   │   └── my-post/  
  │   │       ├── index.md  
  │   │       ├── featured.jpg.webp  
  │   │       └── image.png.webp  
  │   └── products/  
  │       └── my-product/  
  │           ├── index.md  
  │           └── product-image.jpg.webp  
  └── static/         # Preserves original Hugo static assets  
  ```  


## 📌 Notes  

1. **Image Handling**:  
   - The plugin automatically downloads images from the WordPress media library (requires server write permissions).  
   - Remote images (non-WordPress domains) may require additional cross-origin permissions.  

2. **Hugo Compatibility**:  
   - The exported Markdown is compatible with basic Hugo syntax. Recommended for Hugo `v0.110+`.  
   - The image shortcode requires theme support for the `img` shortcode, or modify it to use native `<img>` tags.  

3. **WooCommerce Support**:  
   - Requires WooCommerce plugin to be installed and activated.  
   - Product data (e.g., price, stock) must be implemented via Hugo custom fields or theme logic.  


## 🛠 Development Team  
- **Author**: Chris Peng  
- **Website**: https://shopaii.com  
- **Support**: Submit tickets via the WordPress plugin page or email contact@shopaii.com.  


## 📄 License  
This plugin is released under the GPLv2 license, allowing free modification and distribution.  

---  
**Get Started Today**: Install the plugin and start your WordPress to Hugo migration! 🚀
