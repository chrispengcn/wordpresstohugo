
# WordPress to Hugo Exporter Pro

将WordPress文章、页面和产品导出为Hugo静态网站生成器兼容的Markdown文件，支持**Page Bundle结构**和**多格式图片（WebP）**，完美适配Hugo的图片处理规则。


## 🌟 核心功能

### 1. **Hugo Page Bundle结构**
- 导出为标准的Hugo Page Bundle格式：
  ```
  content/
  └── {类型}/          # post/pages/products
      └── {slug}/      # 文章/页面/产品slug
          ├── index.md  # Markdown内容
          └── {图片文件} # 直接保存图片（如 .jpg.webp）
  ```
- 自动生成`index.md`，包含YAML元数据和内容。

### 2. **多格式图片支持**
- 提取WordPress内容中的所有图片（包括特色图片），下载并保存为`.jpg.webp`、`.png.webp`等格式。
- 自动替换Markdown中的图片链接为Hugo短代码：
  ```markdown
  {{< img src="image.jpg" alt="图片描述" >}}
  ```
  Hugo会自动识别同目录下的`.webp`文件，优先加载WebP格式。

### 3. **元数据完整迁移**
- 支持迁移以下信息：
  - 标题、Slug、发布时间
  - 分类（Categories）、标签（Tags）
  - 特色图片、内容中的图片
  - WooCommerce产品数据（SKU、价格、描述等）
- 生成标准的Hugo YAML Front Matter：
  ```yaml
  ---
  layout: post
  title: "文章标题"
  slug: "my-post"
  date: "2023-10-01 12:00:00"
  categories:
    - 技术
  tags:
    - Hugo
    - WordPress
  featuredImage: "featured.jpg.webp"
  ---
  ```

### 4. **灵活的内容类型支持**
- 支持导出文章（Post）、页面（Page）、WooCommerce产品（Product）。
- 可通过筛选器选择导出单一类型或全部类型内容。


## 🚀 使用流程

### 1. 安装插件
- 下载插件文件或通过WordPress后台“插件 > 安装插件”搜索上传。
- 激活插件后，导航至“仪表盘 > Hugo导出”。

### 2. 配置导出参数
- **基础导出目录**：设置Hugo项目的根目录（如`/var/www/hugo/`）。
- **内容类型**：选择需要导出的内容类型（文章/页面/产品/全部）。
- **包含分类目录**（可选）：按分类生成多级目录（如`posts/categories/技术/my-post/`）。

### 3. 开始导出
- 点击“开始导出”，插件将自动处理内容并显示进度日志。
- 导出完成后，目录结构如下：
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
  └── static/         # 保留原始Hugo静态资源
  ```


## 📌 注意事项

1. **图片处理**：
   - 插件会自动下载WordPress媒体库中的图片（需确保服务器有文件写入权限）。
   - 远程图片（非WordPress域名）可能需要额外的跨域权限。

2. **Hugo兼容性**：
   - 导出的Markdown兼容Hugo的基本语法，建议搭配Hugo `v0.110+` 使用。
   - 图片短代码需在Hugo主题中支持`img`短代码，或自行修改为原生`<img>`标签。

3. **WooCommerce支持**：
   - 需提前安装并激活WooCommerce插件。
   - 产品数据（如价格、库存）需通过Hugo自定义字段或主题逻辑实现。


## 🛠 开发团队

- **作者**：Chris Peng
- **官网**：https://shopaii.com
- **问题反馈**：在WordPress插件页面提交工单或发送邮件至contact@shopaii.com。


## 📄 许可证

本插件基于GPLv2协议发布，允许自由修改和分发。

---

**立即体验**：安装插件并开始你的WordPress到Hugo迁移之旅！ 🚀