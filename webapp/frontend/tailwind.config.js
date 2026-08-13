/**
 * Token lấy từ frontmatter của `webapp/DESIGN.md` — hệ "bàn đọc tối".
 *
 * Bảng màu mặc định của Tailwind bị loại hẳn: ngân sách màu là đúng những gì khai
 * dưới đây. Đặc biệt `slate` chỉ còn ba bậc dùng cho chữ (300/400 và trắng) cộng hai
 * bậc tối chỉ dùng cho viền và nền — `slate-500` và `slate-600` trượt WCAG AA trên
 * nền này (3,82:1 và 2,40:1) nên chúng KHÔNG có mặt như màu chữ. Bản bolt gốc dùng
 * đúng hai màu đó cho chữ nhỏ; đây là chỗ duy nhất hệ này cố ý lệch khỏi nó.
 */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    colors: {
      transparent: 'transparent',
      current: 'currentColor',
      white: '#FFFFFF',
      black: '#000000',

      // Nền, từ sâu nhất tới nổi nhất.
      pacs: {
        950: '#070A13',
        900: '#0B1020',
        850: '#0F1525',
        800: '#141B2E',
        700: '#1C2540',
        600: '#283357',
      },

      accent: { DEFAULT: '#22D3EE', glow: '#67E8F9' },

      // Chữ. 400 là SÀN — không thêm bậc nào tối hơn vào nhóm này.
      slate: { 300: '#CBD5E1', 400: '#94A3B8' },

      // Trạng thái. Mỗi màu một nghĩa, không dùng chéo.
      ok: { DEFAULT: '#34D399', soft: '#6EE7B7' },
      warn: { DEFAULT: '#FBBF24', soft: '#FCD34D' },
      danger: { DEFAULT: '#FB7185', soft: '#FDA4AF' },

      // Vùng chú giải trên ảnh (mask tổn thương của bộ dữ liệu). CỐ Ý nằm ngoài cả
      // bảng bảy lớp lẫn bảng trạng thái: mask KHÔNG phải một lớp và KHÔNG phải một
      // trạng thái. Dùng màu lớp cho nó — ví dụ #38BDF8 của "nang" — sẽ khiến người
      // xem đọc vùng khoanh thành một chẩn đoán.
      annotation: { DEFAULT: '#E879F9', soft: '#F5D0FE' },

      // Heatmap độ nhạy của MÔ HÌNH. Phải khác hẳn `annotation` ở trên: một
      // cái là vùng người chú giải khoanh (ground truth), một cái là chỗ mô hình
      // nhạy (phỏng đoán, có thể sai hoàn toàn). Lẫn hai thứ này là hiểu nhầm tệ
      // nhất app có thể gây ra, nên chúng nằm ở hai phía đối diện của vòng màu.
      attention: { DEFAULT: '#F59E0B', soft: '#FCD34D' },

      // Bảy lớp tổn thương. Ác = dải ấm, lành = dải lạnh; đây là tuyến mã hoá THỨ
      // HAI, luôn đi kèm nhãn chữ. Chỉ dùng trong biểu đồ và dải chú giải.
      lesion: {
        hcc: '#EF4444',
        metastasis: '#F97316',
        icc: '#FB7185',
        fnh: '#22C55E',
        hemangioma: '#14B8A6',
        cyst: '#38BDF8',
        abscess: '#A3E635',
      },
    },

    fontFamily: {
      sans: ['Segoe UI Variable', 'Segoe UI', 'system-ui', 'sans-serif'],
      mono: ['JetBrains Mono', 'ui-monospace', 'Consolas', 'monospace'],
    },

    extend: {
      fontSize: {
        label: ['0.6875rem', { lineHeight: '1.35', letterSpacing: '0.05em' }],
        data: ['0.75rem', { lineHeight: '1.4' }],
        metric: ['1.875rem', { lineHeight: '1.1' }],
      },
      // Workstation: controls remain easy to target but no longer read as soft cards.
      borderRadius: { panel: '0.375rem', control: '0.25rem', frame: '0.375rem' },
      boxShadow: {
        // Chỉ cho hành động chính lúc hover và vùng thả file đang active.
        // Không rải lên panel tĩnh (`webapp/DESIGN.md`, mục Shapes & Depth).
        glow: '0 0 24px -4px rgba(34, 211, 238, 0.45)',
        'glow-soft': '0 0 40px -8px rgba(34, 211, 238, 0.25)',
      },
      maxWidth: { shell: '1600px', measure: '68ch' },
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'pulse-soft': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.55' },
        },
      },
      animation: {
        // `scan` của bản bolt bị bỏ: hiệu ứng quét không giải thích chuyển trạng
        // thái nào, nó chỉ để trông có vẻ kỹ thuật.
        'fade-in': 'fade-in 0.35s ease-out both',
        'pulse-soft': 'pulse-soft 1.8s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};
