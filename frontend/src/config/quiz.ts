export interface QuizOption {
  id: string;
  label: string;
  description?: string;
  icon?: string;
}

export interface QuizQuestion {
  id: string;
  title: string;
  subtitle?: string;
  options: QuizOption[];
  // map to the backend key
  backendKey: 'gender' | 'apparel' | 'activity' | 'weather' | 'vibe';
}

export const quizQuestions: QuizQuestion[] = [
  {
    id: 'q1',
    title: 'لمن تبحث عن العطر؟',
    subtitle: 'نود تخصيص النتائج لتناسب ذوقك تماماً',
    backendKey: 'gender',
    options: [
      { id: 'رجالي', label: 'رجالي', description: 'عطور ذكورية فاخرة' },
      { id: 'نسائي', label: 'نسائي', description: 'عطور أنثوية رقيقة' },
      { id: 'للجنسين', label: 'للجنسين', description: 'مناسبة للجميع' }
    ]
  },
  {
    id: 'q2',
    title: 'ما هو أسلوب ملابسك المفضل؟',
    subtitle: 'يساعدنا هذا في تحديد شخصية العطر',
    backendKey: 'apparel',
    options: [
      { id: 'suit', label: 'رسمي وأنيق', description: 'بدلات وملابس كلاسيكية' },
      { id: 'casual', label: 'كاجوال ومريح', description: 'ملابس يومية مريحة' },
      { id: 'sport', label: 'رياضي وعملي', description: 'ملابس رياضية ونشاط' }
    ]
  },
  {
    id: 'q3',
    title: 'أين ستستخدم العطر غالباً؟',
    subtitle: 'ليتناسب الفوحان مع بيئتك المحيطة',
    backendKey: 'activity',
    options: [
      { id: 'office', label: 'العمل والمكتب', description: 'روائح نظيفة وغير مزعجة' },
      { id: 'outdoor', label: 'خروجات نهارية', description: 'منعش ومناسب للأماكن المفتوحة' },
      { id: 'nightout', label: 'سهرات ومناسبات', description: 'فوحان عالي وجاذبية قصوى' }
    ]
  },
  {
    id: 'q4',
    title: 'ما هي الأجواء المفضلة لك؟',
    subtitle: 'لاختيار النوتات العطرية الملائمة',
    backendKey: 'weather',
    options: [
      { id: 'cold', label: 'أجواء شتوية باردة', description: 'توابل، عود، أخشاب، ودفء' },
      { id: 'hot', label: 'أجواء صيفية حارة', description: 'حمضيات، بحر، وانتعاش' }
    ]
  },
  {
    id: 'q5',
    title: 'أي طابع يعبر عنك أكثر؟',
    subtitle: 'هذا السؤال يحدد البصمة النهائية للعطر',
    backendKey: 'vibe',
    options: [
      { id: 'mysterious', label: 'غامض وجذاب', description: 'بخور، جلود، ورائحة عميقة' },
      { id: 'bold', label: 'جريء وقوي', description: 'قوة انتشار وحضور طاغٍ' },
      { id: 'clean', label: 'نظيف وهادئ', description: 'مسك، بودرة، ونظافة' }
    ]
  }
];
