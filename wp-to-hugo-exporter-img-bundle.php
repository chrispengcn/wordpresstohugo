<?php
/**
 * Plugin Name: WordPress to Hugo Exporter Pro (Page Bundle版)
 * Plugin URI: https://example.com/wordpress-to-hugo-exporter
 * Description: 将WordPress内容导出为Hugo Page Bundle格式，支持图片多格式
 * Version: 2.2.0
 * Author: Chris Peng
 * Author URI: https://shopaii.com
 * License: GPL-2.0+
 */

if (!defined('ABSPATH')) exit;

class WpToHugoExporter {
    private static $instance;
    private $plugin_path;
    private $plugin_url;

    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function __construct() {
        $this->plugin_path = plugin_dir_path(__FILE__);
        $this->plugin_url = plugin_dir_url(__FILE__);

        add_action('admin_menu', array($this, 'add_admin_menu'));
        add_action('wp_ajax_wp_to_hugo_export', array($this, 'ajax_export_posts'));
    }

    public function add_admin_menu() {
        add_menu_page(
            'Hugo导出工具',
            'Hugo导出',
            'manage_options',
            'wp-to-hugo-exporter',
            array($this, 'render_admin_page'),
            'dashicons-archive',
            30
        );
    }

    public function render_admin_page() {
        ?>
        <div class="wrap">
            <h1>Hugo导出工具 Pro</h1>
            
            <div class="notice notice-info">
                <p>使用此工具将您的WordPress内容导出为Hugo兼容的Markdown文件。</p>
                <p>文章、页面和产品将使用Page Bundle结构，并支持图片多格式。</p>
            </div>
            
            <form id="wp-to-hugo-export-form">
                <table class="form-table">
                    <tbody>
                        <tr>
                            <th scope="row">基础导出目录</th>
                            <td>
                                <input type="text" name="base_export_dir" id="base_export_dir" value="<?php echo ABSPATH . 'wp-content/hugo/'; ?>" class="regular-text" />
                                <p class="description">内容将按类型保存到该目录下的子目录：posts、pages、products</p>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row">内容类型</th>
                            <td>
                                <select name="post_type" id="post_type">
                                    <option value="post">文章</option>
                                    <option value="page">页面</option>
                                    <option value="product">产品 (WooCommerce)</option>
                                    <option value="any">所有类型</option>
                                </select>
                                <p class="description">选择要导出的内容类型。</p>
                            </td>
                        </tr>
                    </tbody>
                </table>
                
                <p class="submit">
                    <button type="submit" class="button button-primary" id="export-button">
                        <span class="dashicons dashicons-download"></span> 开始导出
                    </button>
                </p>
            </form>
            
            <div id="export-results" style="margin-top: 20px; display: none;">
                <h3>导出结果</h3>
                <div id="export-log" style="background: #f9f9f9; border: 1px solid #ddd; padding: 10px; max-height: 400px; overflow-y: auto;"></div>
                <div id="export-summary" style="margin-top: 10px;"></div>
            </div>
        </div>
        
        <script type="text/javascript">
            jQuery(document).ready(function($) {
                $('#wp-to-hugo-export-form').on('submit', function(e) {
                    e.preventDefault();
                    
                    // 准备导出参数
                    var base_export_dir = $('#base_export_dir').val();
                    var post_type = $('#post_type').val();
                    
                    // 显示结果区域
                    $('#export-results').show();
                    $('#export-log').html('');
                    $('#export-summary').html('');
                    
                    // 禁用导出按钮
                    $('#export-button').attr('disabled', true);
                    $('#export-button').html('<span class="dashicons dashicons-update spin"></span> 导出中...');
                    
                    // 执行导出
                    $.ajax({
                        url: ajaxurl,
                        type: 'POST',
                        data: {
                            action: 'wp_to_hugo_export',
                            base_export_dir: base_export_dir,
                            post_type: post_type
                        },
                        xhrFields: {
                            onprogress: function(e) {
                                var data = e.currentTarget.response;
                                if (data) {
                                    $('#export-log').html(data);
                                    // 滚动到底部
                                    $('#export-log').scrollTop($('#export-log')[0].scrollHeight);
                                }
                            }
                        },
                        success: function(response) {
                            $('#export-log').html(response.log);
                            $('#export-summary').html(response.summary);
                            $('#export-button').html('<span class="dashicons dashicons-yes"></span> 导出完成');
                        },
                        error: function() {
                            $('#export-log').append('<div class="error">导出过程中发生错误。</div>');
                            $('#export-button').html('<span class="dashicons dashicons-no"></span> 导出失败');
                        },
                        complete: function() {
                            // 启用导出按钮
                            $('#export-button').attr('disabled', false);
                            // 滚动到底部
                            $('#export-log').scrollTop($('#export-log')[0].scrollHeight);
                        }
                    });
                });
            });
        </script>
        <?php
    }

    public function ajax_export_posts() {
        if (!current_user_can('manage_options')) {
            wp_send_json_error('您没有执行此操作的权限。');
        }
        
        $base_export_dir = sanitize_text_field($_POST['base_export_dir']);
        $post_type = sanitize_text_field($_POST['post_type']);
        
        $type_config = array(
            'post'    => array('layout' => 'post',    'dir' => 'posts'),
            'page'    => array('layout' => 'page',    'dir' => 'pages'),
            'product' => array('layout' => 'product', 'dir' => 'products')
        );
        
        ob_start();
        
        $log = '';
        $export_count = 0;
        $error_count = 0;
        
        $args = array(
            'post_type'      => $post_type,
            'post_status'    => 'publish',
            'posts_per_page' => -1,
            'orderby'        => 'date',
            'order'          => 'DESC'
        );
        
        $query = new WP_Query($args);
        
        if ($query->have_posts()) {
            echo '<div class="updated">开始导出内容...</div>';
            
            while ($query->have_posts()) {
                $query->the_post();
                
                $post_id = get_the_ID();
                $post_type = get_post_type($post_id);
                
                if ($post_type === 'any') {
                    continue;
                }
                
                if (!isset($type_config[$post_type])) {
                    echo "<div class=\"warning\">未知内容类型: {$post_type}，已跳过</div>";
                    continue;
                }
                
                $config = $type_config[$post_type];
                $layout = $config['layout'];
                $type_dir = $config['dir'];
                
                try {
                    $title = get_the_title();
                    $slug = get_post_field('post_name', $post_id);
                    $date = get_the_date('Y-m-d H:i:s');
                    $content = get_the_content();
                    $permalink = get_permalink();
                    
                    $content = apply_filters('the_content', $content);
                    $content = str_replace(']]>', ']]&gt;', $content);
                    
                    $date_obj = DateTime::createFromFormat('Y-m-d H:i:s', $date);
                    $date_str = $date_obj->format('Y-m-d');
                    
                    // 构建Page Bundle目录结构
                    $export_dir = trailingslashit($base_export_dir) . 
                        "content/{$type_dir}/{$slug}/";
                    
                    // 创建目录
                    wp_mkdir_p($export_dir);
                    
                    // 提取内容中的图片URL
                    $image_urls = array();
                    $pattern = '/<img[^>]+src="([^"]+)"/i';
                    preg_match_all($pattern, $content, $matches);
                    if (!empty($matches[1])) {
                        $image_urls = array_unique($matches[1]);
                    }
                    
                    // 处理特色图片
                    $featured_image_id = get_post_thumbnail_id($post_id);
                    $featured_img_url = '';
                    if ($featured_image_id) {
                        $featured_img_url = wp_get_attachment_url($featured_image_id);
                        $image_urls[] = $featured_img_url;
                    }
                    
                    // 下载图片并保存到export_dir目录
                    $local_images = array();
                    foreach ($image_urls as $img_url) {
                        if (empty($img_url)) continue;
                        
                        // 处理相对URL
                        if (strpos($img_url, '//') === false) {
                            $img_url = home_url($img_url);
                        }
                        
                        // 获取文件名和扩展名
                        $parsed 获取文件名和扩展名
                        $parsed_url = parse_url($img_url);
                        $path = $parsed_url['path'];
                        $img_filename = basename($path);
                        $img_info = pathinfo($img_filename);
                        $img_base = $img_info['filename'];
                        $img_ext = strtolower($img_info['extension']);
                        
                        // 确保扩展名有效
                        $valid_exts = array('jpg', 'jpeg', 'png', 'gif', 'bmp');
                        if (!in_array($img_ext, $valid_exts)) {
                            $img_ext = 'jpg'; // 默认使用jpg
                        }
                        
                        // 生成WebP格式的文件名
                        $webp_filename = "{$img_base}.{$img_ext}.webp";
                        $local_path = $webp_filename; // 直接保存到当前目录
                        $local_full_path = "{$export_dir}{$webp_filename}";
                        
                        // 尝试下载图片
                        try {
                            $response = wp_remote_get($img_url, array('timeout' => 30));
                            
                            if (is_wp_error($response)) {
                                echo "<div class=\"warning\">下载失败: {$img_url} - {$response->get_error_message()}</div>";
                                continue;
                            }
                            
                            $status_code = wp_remote_retrieve_response_code($response);
                            if ($status_code != 200) {
                                echo "<div class=\"warning\">下载失败: {$img_url} (状态码: {$status_code})</div>";
                                continue;
                            }
                            
                            $img_content = wp_remote_retrieve_body($response);
                            if (empty($img_content)) {
                                echo "<div class=\"warning\">下载失败: {$img_url} (内容为空)</div>";
                                continue;
                            }
                            
                            // 保存图片
                            file_put_contents($local_full_path, $img_content);
                            $local_images[] = $local_path;
                            
                            echo "<div class=\"updated\">已下载图片: {$webp_filename}</div>";
                        } catch (Exception $e) {
                            echo "<div class=\"error\">下载图片时出错: {$img_url} - {$e->getMessage()}</div>";
                        }
                    }
                    
                    // 获取分类和标签
                    $categories = get_the_category($post_id);
                    $category_names = array();
                    if (!empty($categories)) {
                        foreach ($categories as $cat) {
                            $category_names[] = $cat->name;
                        }
                    }
                    
                    $tags = get_the_tags($post_id);
                    $tag_names = array();
                    if ($tags) {
                        foreach ($tags as $tag) {
                            $tag_names[] = $tag->name;
                        }
                    }
                    
                    // 构建Markdown文件内容
                    $md_content = "---\n";
                    $md_content .= "layout: {$layout}\n";
                    $md_content .= "title: \"{$this->escape_yaml_string($title)}\"\n";
                    $md_content .= "slug: \"{$slug}\"\n";
                    $md_content .= "date: {$date}\n";
                    
                    if (!empty($category_names)) {
                        $md_content .= "categories:\n";
                        foreach ($category_names as $cat_name) {
                            $md_content .= "- {$this->escape_yaml_string($cat_name)}\n";
                        }
                    }
                    
                    if (!empty($tag_names)) {
                        $md_content .= "tags:\n";
                        foreach ($tag_names as $tag_name) {
                            $md_content .= "- {$this->escape_yaml_string($tag_name)}\n";
                        }
                    }
                    
                    if (!empty($featured_img_url) && in_array(basename(parse_url($featured_img_url, PHP_URL_PATH)) . ".webp", $local_images)) {
                        $featured_local_path = basename(parse_url($featured_img_url, PHP_URL_PATH)) . ".webp";
                        $md_content .= "featuredImage: {$featured_local_path}\n";
                    }
                    
                    if (!empty($local_images)) {
                        $md_content .= "images:\n";
                        foreach ($local_images as $img_path) {
                            $md_content .= "- {$img_path}\n";
                        }
                    }
                    
                    // 如果是产品类型，添加额外的产品字段
                    if ($post_type === 'product') {
                        if (class_exists('WooCommerce')) {
                            $product = wc_get_product($post_id);
                            
                            $sku = $product->get_sku() ? $product->get_sku() : '';
                            $md_content .= "sku: \"{$this->escape_yaml_string($sku)}\"\n";
                            
                            $product_cats = wp_get_post_terms($post_id, 'product_cat', array('fields' => 'names'));
                            if (!empty($product_cats)) {
                                $md_content .= "product_categories:\n";
                                foreach ($product_cats as $cat) {
                                    $md_content .= "- {$this->escape_yaml_string($cat)}\n";
                                }
                            }
                            
                            $product_tags = wp_get_post_terms($post_id, 'product_tag', array('fields' => 'names'));
                            if (!empty($product_tags)) {
                                $md_content .= "product_tags:\n";
                                foreach ($product_tags as $tag) {
                                    $md_content .= "- {$this->escape_yaml_string($tag)}\n";
                                }
                            }
                            
                            $buy_link = get_post_meta($post_id, '_buy_link', true);
                            if ($buy_link) {
                                $md_content .= "buy_link: {$this->escape_yaml_string($buy_link)}\n";
                            }
                            
                            $short_description = $product->get_short_description();
                            if ($short_description) {
                                $escaped_description = $this->escape_yaml_string($short_description);
                                $md_content .= "description: >\n  {$escaped_description}\n";
                            }
                        }
                    }
                    
                    $md_content .= "---\n\n";
                    
                    // 替换内容中的图片URL为相对路径
                    foreach ($image_urls as $img_url) {
                        $img_filename = basename(parse_url($img_url, PHP_URL_PATH));
                        $img_info = pathinfo($img_filename);
                        $img_base = $img_info['filename'];
                        $img_ext = strtolower($img_info['extension']);
                        
                        if (!in_array($img_ext, array('jpg', 'jpeg', 'png', 'gif', 'bmp'))) {
                            continue;
                        }
                        
                        $webp_filename = "{$img_base}.{$img_ext}.webp";
                        
                        // 替换图片URL为Hugo图片短代码
                        $img_tag = '<img[^>]+src="' . preg_quote($img_url, '/') . '"[^>]*>';
                        $alt_text = '图片';
                        
                        // 尝试从原图片标签中提取alt文本
                        preg_match('/alt="([^"]*)"/i', $img_content, $alt_matches);
                        if (!empty($alt_matches[1])) {
                            $alt_text = $alt_matches[1];
                        }
                        
                        $replacement = '{{< img src="' . $webp_filename . '" alt="' . $alt_text . '" >}}';
                        $content = preg_replace('/' . $img_tag . '/i', $replacement, $content);
                    }
                    
                    $md_content .= $content;
                    
                    // 写入index.md文件
                    $file_path = "{$export_dir}index.md";
                    $result = file_put_contents($file_path, $md_content);
                    
                    if ($result !== false) {
                        echo "<div class=\"updated\">已导出: {$slug} (类型: {$post_type})</div>";
                        $export_count++;
                    } else {
                        echo "<div class=\"error\">导出失败: {$slug} (类型: {$post_type})</div>";
                        $error_count++;
                    }
                } catch (Exception $e) {
                    echo "<div class=\"error\">处理 {$post_id} 时出错: {$e->getMessage()}</div>";
                    $error_count++;
                }
                
                ob_flush();
                flush();
            }
            
            wp_reset_postdata();
            
            $summary = "<div class=\"updated\">导出完成！共处理 {$query->post_count} 个项目，成功导出 {$export_count} 个，失败 {$error_count} 个。</div>";
        } else {
            $summary = "<div class=\"error\">没有找到可导出的内容。</div>";
        }
        
        $log = ob_get_clean();
        
        wp_send_json(array(
            'log'     => $log,
            'summary' => $summary
        ));
    }
    
    private function escape_yaml_string($str) {
        $str = str_replace('"', '\\"', $str);
        $str = preg_replace('/\n/', '\n  ', $str);
        return $str;
    }
}

function wp_to_hugo_exporter_init() {
    WpToHugoExporter::get_instance();
}
add_action('plugins_loaded', 'wp_to_hugo_exporter_init');