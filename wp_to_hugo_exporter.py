#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import pymysql
import datetime
import html
import argparse
from pathlib import Path

class WpToHugoExporter:
    """WordPress到Hugo导出工具"""
    
    def __init__(self, wp_root):
        """初始化导出工具"""
        self.wp_root = wp_root
        self.config_file = os.path.join(wp_root, 'wp-config.php')
        self.base_export_dir = os.path.join(wp_root, 'wp-content', 'md')
        self.db_config = {}
        self.db_prefix = 'wp_'
        self.type_config = {
            'post': {'layout': 'post', 'dir': 'posts'},
            'page': {'layout': 'page', 'dir': 'pages'},
            'product': {'layout': 'product', 'dir': 'products'}
        }
        self.export_count = 0
        self.error_count = 0
    
    def read_wp_config(self):
        """读取WordPress配置文件获取数据库信息"""
        print(f"正在读取WordPress配置文件: {self.config_file}")
        
        if not os.path.exists(self.config_file):
            print(f"错误: WordPress配置文件不存在: {self.config_file}")
            return False
        
        with open(self.config_file, 'r') as f:
            content = f.read()
        
        # 提取数据库配置
        db_name = self._extract_config_value(content, 'DB_NAME')
        db_user = self._extract_config_value(content, 'DB_USER')
        db_password = self._extract_config_value(content, 'DB_PASSWORD')
        db_host = self._extract_config_value(content, 'DB_HOST') or 'localhost'
        
        if not all([db_name, db_user, db_password]):
            print("错误: 无法从配置文件中提取完整的数据库信息")
            return False
        
        # 提取数据库表前缀
        prefix_match = re.search(r"^\$table_prefix\s*=\s*['\"]([^'\"]+)['\"]\s*;", content, re.MULTILINE)
        if prefix_match:
            self.db_prefix = prefix_match.group(1)
        
        self.db_config = {
            'host': db_host,
            'user': db_user,
            'password': db_password,
            'db': db_name,
            'charset': 'utf8mb4'
        }
        
        print(f"成功读取数据库配置: {db_name}@{db_host}")
        print(f"数据库表前缀: {self.db_prefix}")
        return True
    
    def _extract_config_value(self, content, constant_name):
        """从配置文件内容中提取常量值"""
        pattern = r"^\s*define\(\s*['\"]" + constant_name + r"['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)\s*;"
        match = re.search(pattern, content, re.MULTILINE)
        return match.group(1) if match else None
    
    def connect_db(self):
        """连接到WordPress数据库"""
        try:
            self.connection = pymysql.connect(**self.db_config)
            print("成功连接到数据库")
            return True
        except pymysql.Error as e:
            print(f"数据库连接失败: {e}")
            return False
    
    def export_content(self, post_type='any'):
        """导出指定类型的内容"""
        print(f"开始导出内容 (类型: {post_type})...")
        
        # 确保导出目录存在
        content_dir = os.path.join(self.base_export_dir, 'content')
        for config in self.type_config.values():
            os.makedirs(os.path.join(content_dir, config['dir']), exist_ok=True)
        
        try:
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                # 构建查询条件
                where_clause = ""
                if post_type != 'any':
                    where_clause = f"AND post_type = '{post_type}'"
                else:
                    # 只查询post, page, product类型
                    where_clause = "AND post_type IN ('post', 'page', 'product')"
                
                # 查询文章
                query = f"""
                SELECT * FROM {self.db_prefix}posts 
                WHERE post_status = 'publish' {where_clause}
                ORDER BY post_date DESC
                """
                cursor.execute(query)
                posts = cursor.fetchall()
                
                print(f"找到 {len(posts)} 个可导出的项目")
                
                for post in posts:
                    try:
                        self.export_post(post)
                    except Exception as e:
                        print(f"处理文章 ID {post['ID']} 时出错: {e}")
                        self.error_count += 1
        
        except pymysql.Error as e:
            print(f"数据库查询错误: {e}")
            return False
        
        print(f"导出完成！共处理 {len(posts)} 个项目，成功导出 {self.export_count} 个，失败 {self.error_count} 个。")
        return True
    
    def export_post(self, post):
        """导出单个文章"""
        post_id = post['ID']
        post_type = post['post_type']
        
        # 跳过未知类型
        if post_type not in self.type_config:
            print(f"警告: 未知内容类型 '{post_type}'，已跳过")
            return
        
        config = self.type_config[post_type]
        layout = config['layout']
        type_dir = config['dir']
        
        # 构建导出目录
        export_dir = os.path.join(self.base_export_dir, 'content', type_dir)
        
        # 获取文章基本信息
        title = post['post_title']
        slug = post['post_name']
        date = post['post_date']
        content = post['post_content']
        permalink = f"/{slug}/"  # 简化的永久链接
        
        # 格式化日期
        # 检查date是否已经是datetime对象
        if isinstance(date, datetime.datetime):
            date_str = date.strftime('%Y-%m-%d')
        else:
            date_obj = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            date_str = date_obj.strftime('%Y-%m-%d')
        
        # 生成文件名
        filename = f"{date_str}-{slug}.md"
        file_path = os.path.join(export_dir, filename)
        
        # 获取分类
        categories = self.get_categories(post_id)
        
        # 获取标签
        tags = self.get_tags(post_id)
        
        # 获取特色图片
        featured_image = self.get_featured_image(post_id)
        
        # 构建Markdown文件内容
        md_content = "---\n"
        md_content += f"layout: {layout}\n"
        md_content += f"title: \"{self.escape_yaml_string(title)}\"\n"
        md_content += f"slug: \"{slug}\"\n"
        md_content += f"permalink: \"{permalink}\"\n"
        md_content += f"date: {date}\n"
        
        # 分类
        if categories:
            md_content += "categories:\n"
            for category in categories:
                md_content += f"- {self.escape_yaml_string(category)}\n"
        else:
            md_content += "categories: []\n"
        
        # 特色图片
        md_content += f"featureImage: {featured_image}\n"
        md_content += f"image: {featured_image}\n"
        
        # 标签
        if tags:
            md_content += "tags: [" + ", ".join([f'"{self.escape_yaml_string(tag)}"' for tag in tags]) + "]\n"
        else:
            md_content += "tags: []\n"
        
        # 如果是产品类型，添加额外的产品字段
        if post_type == 'product':
            md_content += self.get_product_metadata(post_id)
        
        md_content += "---\n\n"
        
        # 处理内容
        content = self.process_content(content)
        md_content += content
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"已导出: {filename} (类型: {post_type})")
        self.export_count += 1
    
    def get_categories(self, post_id):
        """获取文章分类"""
        categories = []
        try:
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                query = f"""
                SELECT t.name 
                FROM {self.db_prefix}terms t
                JOIN {self.db_prefix}term_taxonomy tt ON t.term_id = tt.term_id
                JOIN {self.db_prefix}term_relationships tr ON tt.term_taxonomy_id = tr.term_taxonomy_id
                WHERE tr.object_id = %s AND tt.taxonomy = 'category'
                """
                cursor.execute(query, (post_id,))
                results = cursor.fetchall()
                categories = [result['name'] for result in results]
        except pymysql.Error:
            pass
        return categories
    
    def get_tags(self, post_id):
        """获取文章标签"""
        tags = []
        try:
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                query = f"""
                SELECT t.name 
                FROM {self.db_prefix}terms t
                JOIN {self.db_prefix}term_taxonomy tt ON t.term_id = tt.term_id
                JOIN {self.db_prefix}term_relationships tr ON tt.term_taxonomy_id = tr.term_taxonomy_id
                WHERE tr.object_id = %s AND tt.taxonomy = 'post_tag'
                """
                cursor.execute(query, (post_id,))
                results = cursor.fetchall()
                tags = [result['name'] for result in results]
        except pymysql.Error:
            pass
        return tags
    
    def get_featured_image(self, post_id):
        """获取特色图片URL"""
        try:
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                # 获取特色图片ID
                query = f"SELECT meta_value FROM {self.db_prefix}postmeta WHERE post_id = %s AND meta_key = '_thumbnail_id'"
                cursor.execute(query, (post_id,))
                result = cursor.fetchone()
                
                if result and result['meta_value']:
                    thumbnail_id = result['meta_value']
                    # 获取图片URL
                    query = f"SELECT guid FROM {self.db_prefix}posts WHERE ID = %s"
                    cursor.execute(query, (thumbnail_id,))
                    img_result = cursor.fetchone()
                    if img_result:
                        return img_result['guid']
        except pymysql.Error:
            pass
        return ""
    
    def get_product_metadata(self, post_id):
        """获取产品元数据"""
        metadata = ""
        try:
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                # 获取SKU
                query = f"SELECT meta_value FROM {self.db_prefix}postmeta WHERE post_id = %s AND meta_key = '_sku'"
                cursor.execute(query, (post_id,))
                result = cursor.fetchone()
                sku = result['meta_value'] if result else ""
                metadata += f"sku: \"{self.escape_yaml_string(sku)}\"\n"
                
                # 获取产品分类
                query = f"""
                SELECT t.name 
                FROM {self.db_prefix}terms t
                JOIN {self.db_prefix}term_taxonomy tt ON t.term_id = tt.term_id
                JOIN {self.db_prefix}term_relationships tr ON tt.term_taxonomy_id = tr.term_taxonomy_id
                WHERE tr.object_id = %s AND tt.taxonomy = 'product_cat'
                """
                cursor.execute(query, (post_id,))
                results = cursor.fetchall()
                product_cats = [result['name'] for result in results]
                
                metadata += "product_categories:\n"
                for cat in product_cats:
                    metadata += f"- {self.escape_yaml_string(cat)}\n"
                
                # 获取产品标签
                query = f"""
                SELECT t.name 
                FROM {self.db_prefix}terms t
                JOIN {self.db_prefix}term_taxonomy tt ON t.term_id = tt.term_id
                JOIN {self.db_prefix}term_relationships tr ON tt.term_taxonomy_id = tr.term_taxonomy_id
                WHERE tr.object_id = %s AND tt.taxonomy = 'product_tag'
                """
                cursor.execute(query, (post_id,))
                results = cursor.fetchall()
                product_tags = [result['name'] for result in results]
                
                metadata += "product_tags:\n"
                for tag in product_tags:
                    metadata += f"- {self.escape_yaml_string(tag)}\n"
                
                # 获取购买链接
                query = f"SELECT meta_value FROM {self.db_prefix}postmeta WHERE post_id = %s AND meta_key = '_buy_link'"
                cursor.execute(query, (post_id,))
                result = cursor.fetchone()
                buy_link = result['meta_value'] if result else ""
                
                if buy_link:
                    metadata += f"buy_link: {self.escape_yaml_string(buy_link)}\n"
                
                # 获取产品图片
                query = f"SELECT meta_value FROM {self.db_prefix}postmeta WHERE post_id = %s AND meta_key = '_product_image_gallery'"
                cursor.execute(query, (post_id,))
                result = cursor.fetchone()
                gallery_ids = result['meta_value'].split(',') if result and result['meta_value'] else []
                
                metadata += "images:\n"
                
                # 先添加特色图片
                featured_image = self.get_featured_image(post_id)
                if featured_image:
                    metadata += f"- {featured_image}\n"
                
                # 再添加产品图库图片
                for img_id in gallery_ids:
                    if img_id:
                        try:
                            query = f"SELECT guid FROM {self.db_prefix}posts WHERE ID = %s"
                            cursor.execute(query, (img_id,))
                            img_result = cursor.fetchone()
                            if img_result:
                                metadata += f"- {img_result['guid']}\n"
                        except pymysql.Error:
                            pass
                
                # 获取产品简短描述
                query = f"SELECT meta_value FROM {self.db_prefix}postmeta WHERE post_id = %s AND meta_key = '_short_description'"
                cursor.execute(query, (post_id,))
                result = cursor.fetchone()
                short_description = result['meta_value'] if result else ""
                
                if short_description:
                    escaped_description = self.escape_yaml_string(short_description)
                    metadata += f"description: >\n  {escaped_description}\n"
                
        except pymysql.Error:
            pass
        
        return metadata
    
    def process_content(self, content):
        """处理文章内容"""
        # 这里可以添加更多内容处理逻辑
        # 例如将WordPress的短代码转换为Markdown等
        
        # 简单地转义HTML实体
        content = html.unescape(content)
        
        return content
    
    def escape_yaml_string(self, string):
        """转义YAML字符串"""
        if not string:
            return ""
        
        # 替换双引号
        string = string.replace('"', '\\"')
        
        # 处理多行字符串
        string = re.sub(r'\n', '\\n  ', string)
        
        return string

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='将WordPress内容导出为Hugo兼容的Markdown文件')
    parser.add_argument('--wp-root', required=True, help='WordPress安装根目录')
    parser.add_argument('--type', choices=['post', 'page', 'product', 'any'], default='any', 
                        help='要导出的内容类型 (默认: any)')
    
    args = parser.parse_args()
    
    # 确保目录存在
    wp_root = os.path.abspath(args.wp_root)
    if not os.path.exists(wp_root):
        print(f"错误: 指定的WordPress根目录不存在: {wp_root}")
        sys.exit(1)
    
    print("=" * 50)
    print("WordPress到Hugo导出工具")
    print("=" * 50)
    
    exporter = WpToHugoExporter(wp_root)
    
    # 读取配置
    if not exporter.read_wp_config():
        sys.exit(1)
    
    # 连接数据库
    if not exporter.connect_db():
        sys.exit(1)
    
    # 导出内容
    exporter.export_content(args.type)
    
    # 关闭数据库连接
    exporter.connection.close()
    print("数据库连接已关闭")

if __name__ == "__main__":
    main()
