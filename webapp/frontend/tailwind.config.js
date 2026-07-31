/**
 * Token lấy thẳng từ frontmatter của `webapp/DESIGN.md`.
 *
 * Lớp thị giác được ép ở mức CẤU HÌNH chứ không ở mức kỷ luật: `borderRadius` chỉ
 * có `0`, `boxShadow` chỉ có `none`. Viết `rounded-2xl` hay `shadow-xl` trong JSX
 * sẽ không sinh ra class nào — build hỏng ngay thay vì trôi dần khỏi hệ thống.
 * Đây là bài học từ bản bolt: ràng buộc chỉ nằm trong tài liệu thì không giữ được.
 */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    // `extend` bị bỏ có chủ ý cho colors/radius/shadow: bảng màu mặc định của
    // Tailwind (slate, cyan, rose...) không được phép lọt vào. Ngân sách màu là
    // toàn bộ những gì liệt kê dưới đây.
    colors: {
      transparent: 'transparent',
      current: 'currentColor',
      paper: '#F5F6F4',
      land: '#E4D8B8',
      shoal: { 1: '#DCE9F0', 2: '#B8D4E4', 3: '#8FBBD4' },
      // `tertiary` phải đạt AA trên CẢ giấy lẫn nền buff, vì marginalia xuất hiện
      // trên cả hai. Bản đầu để #75838F: 3,59:1 trên giấy và 2,74:1 trên buff, tức
      // trượt AA ở đúng cỡ chữ nhỏ nhất của hệ thống. #525C66 cho 6,29:1 và 4,81:1.
      ink: { DEFAULT: '#16202A', secondary: '#4A5A66', tertiary: '#525C66' },
      hairline: '#C3CBD1',
      rule: '#8C99A2',
      caution: '#C0247E',
      drying: '#7C9455',
    },
    borderRadius: { none: '0', DEFAULT: '0' },
    boxShadow: { none: 'none' },
    fontFamily: {
      // Hai độ rộng của một superfamily, đúng kỷ luật hải đồ. Cả hai phủ đủ dấu
      // tiếng Việt — ràng buộc quyết định, không phải sở thích.
      narrow: ['Archivo Narrow', 'Arial Narrow', 'Segoe UI', 'system-ui', 'sans-serif'],
      sans: ['Archivo', 'Segoe UI', 'system-ui', 'sans-serif'],
    },
    fontSize: {
      marginalia: ['clamp(0.72rem, 0.95vw, 0.8rem)', { lineHeight: '1.35', letterSpacing: '0.02em' }],
      legend: ['clamp(0.8rem, 1.05vw, 0.88rem)', { lineHeight: '1.4', letterSpacing: '0.015em' }],
      body: ['clamp(0.94rem, 1.3vw, 1.05rem)', { lineHeight: '1.55' }],
      headline: ['clamp(1.25rem, 1.9vw, 1.5rem)', { lineHeight: '1.3' }],
      sounding: ['clamp(1.3rem, 2.1vw, 1.65rem)', { lineHeight: '1.1' }],
      'sounding-lead': ['clamp(1.7rem, 2.9vw, 2.2rem)', { lineHeight: '1.05' }],
      'chart-title': ['clamp(1.75rem, 2.6vw, 2.2rem)', { lineHeight: '1.15', letterSpacing: '0.01em' }],
    },
    spacing: {
      0: '0',
      xs: '4px',
      sm: '8px',
      md: '16px',
      lg: '28px',
      xl: '44px',
      xxl: '72px',
      px: '1px',
      full: '100%',
    },
    extend: {
      borderWidth: { hair: '1px', mark: '2px' },
      maxWidth: { chart: '1600px', measure: '68ch' },
    },
  },
  plugins: [],
};
