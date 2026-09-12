/*!
 * aria-i18n.js — Système de langue global FORGEDIS
 * Une seule inclusion dans chaque page suffit.
 * Ajouter data-i18n="cle" sur n'importe quel élément HTML.
 * Changer la langue : AriaI18n.set('en')
 * Lire un texte : AriaI18n.t('cle')
 */
(function(w) {
'use strict';

// ═══════════════════════════════════════════════════════════
// LANGUES DISPONIBLES
// ═══════════════════════════════════════════════════════════
var LANGUES = [
  { code:'fr', label:'Français',         flag:'🇫🇷', dir:'ltr' },
  { code:'en', label:'English',          flag:'🇬🇧', dir:'ltr' },
  { code:'sa', label:'العربية',          flag:'🇸🇦', dir:'rtl' },
  { code:'dz', label:'العربية (الجزائر)',flag:'🇩🇿', dir:'rtl' },
  { code:'es', label:'Español',          flag:'🇪🇸', dir:'ltr' },
  { code:'pt', label:'Português',        flag:'🇵🇹', dir:'ltr' },
  { code:'de', label:'Deutsch',          flag:'🇩🇪', dir:'ltr' },
  { code:'it', label:'Italiano',         flag:'🇮🇹', dir:'ltr' },
];

// ═══════════════════════════════════════════════════════════
// TRADUCTIONS GLOBALES — portail + pages communes
// ═══════════════════════════════════════════════════════════
var T = {
  fr: {
    ind_deconnexion: 'Déconnexion',
    ind_poste_dirigeant: 'Dirigeant',
    ind_nav_vue_ensemble: 'Vue d’ensemble',
    ind_nav_equipe: 'Équipe',
    ind_nav_pilotage: 'Pilotage financier',
    ind_nav_operations: 'Opérations',
    ind_nav_ia: 'IA & Pilotage',
    ind_nav_config: 'Configuration',
    ind_nav_mon_espace: 'Mon espace',
    ind_brand_sub: 'Poste Dirigeant',
    ind_tableau_bord: 'Tableau de bord',
    ind_salaries: 'Salariés',
    ind_presences: 'Présences',
    ind_absences: 'Absences',
    ind_equipes: 'Équipes & organigramme',
    ind_permissions: 'Permissions salariés',
    ind_facturation: 'Facturation',
    ind_tresorerie: 'Trésorerie',
    ind_bc: 'Bons de commande',
    ind_taches: 'Tâches entreprise',
    ind_tickets: 'Service client',
    ind_stock: 'Stock',
    ind_consulting: 'Consulting Aria',
    ind_reunions: 'Réunions & CR',
    ind_briefing: 'Briefing matinal',
    ind_config: 'Entreprise & config',
    ind_securite: 'Sécurité & accès',
    ind_pointage: 'Pointage',
    ind_mes_conges: 'Mes congés',
    ind_droits: 'Mes droits',
    ind_formation: 'Formation',
    ind_journal: 'Journal',
    // Nav portail
    nav_retour_site: '← Retour au site',
    nav_tableau_bord: 'Tableau de bord',
    nav_abonnement: 'Mon abonnement',
    nav_historique: 'Historique',
    nav_formation: 'Formation',
    nav_fonctionnalites: 'Fonctionnalités',
    nav_parametres: 'Paramètres',
    nav_support: 'Support',
    nav_deconnexion: 'Se déconnecter',
    nav_compte: 'Principal',
    nav_section_compte: 'Compte',
    // Accueil portail
    bonjour: 'Bonjour',
    apercu_mois: "Voici un aperçu de votre utilisation d'Aria ce mois-ci.",
    eco_taches: 'Éco-tâches utilisées',
    forfait_actuel: 'Forfait actuel',
    statut: 'Statut',
    sur_30_mois: 'sur 30 ce mois',
    acces_illimite: 'Accès illimité',
    abonnement_en_cours: 'Abonnement en cours',
    // Téléchargements
    dl_windows_titre: 'Agent Aria pour votre ordinateur',
    dl_windows_desc: "Installez l'agent sur votre PC — Aria pourra ouvrir vos fichiers, naviguer, répondre à vos emails.",
    dl_windows_btn: '⬇ Télécharger pour Windows',
    dl_android_titre: 'Application Aria — Android',
    dl_android_desc: 'Parlez à Aria depuis votre téléphone — elle transmet vos demandes à l\'agent installé sur votre ordinateur.',
    dl_android_btn: '⬇ Télécharger l\'APK Android',
    dl_iphone_titre: 'Application Aria — iPhone',
    dl_iphone_desc: 'La version iPhone d\'Aria est en cours de validation sur l\'App Store Apple.',
    dl_iphone_btn: 'Bientôt disponible',
    // Abonnement
    mon_abonnement: 'Mon abonnement',
    gerer_forfait: 'Gérez votre forfait Aria FORGEDIS.',
    plan_decouverte: 'Découverte',
    plan_facility: 'Aria Facility',
    actions_illimitees: 'Actions illimitées',
    pilotage_pc: 'Pilotage PC complet',
    toutes_langues: 'Toutes les langues',
    assistance_prioritaire: 'Assistance prioritaire',
    donnees_chez_vous: 'Données chez vous',
    bouclier_arnaque: 'Bouclier anti-arnaque',
    resilier: 'Résilier l\'abonnement',
    passer_facility: '⭐ Passer à Aria Facility',
    essai_14j: 'Essayer 14 jours gratuits →',
    // Historique
    historique: 'Historique',
    activite_recente: 'Activité récente',
    connexion_compte: 'Connexion au compte',
    analyse_document: 'Analyse de document',
    abonnement_active: 'Abonnement activé',
    aujourd_hui: "Aujourd'hui",
    cette_semaine: 'Cette semaine',
    ce_mois: 'Ce mois',
    reussi: 'Réussi',
    termine: 'Terminé',
    actif: 'Actif',
    // Paramètres
    parametres: 'Paramètres',
    infos_compte: 'Informations du compte',
    adresse_email: 'Adresse email',
    email_desc: 'Utilisée pour votre abonnement et notifications',
    forfait: 'Forfait',
    forfait_desc: 'Votre abonnement actuel',
    statut_label: 'Statut',
    statut_desc: 'État de votre abonnement',
    eco_ce_mois: 'Éco-tâches ce mois',
    eco_desc: 'Remis à zéro le 1er de chaque mois',
    securite: 'Sécurité',
    token_aria: 'Identifiant Aria (token)',
    token_desc: 'Votre clé d\'accès unique — ne jamais partager',
    chiffrement: 'Chiffrement',
    chiffrement_desc: 'Vos données sont chiffrées en transit',
    chiffrement_actif: '✓ Actif',
    donnees_rgpd: 'Données & RGPD',
    exporter_donnees: 'Exporter mes données',
    exporter_desc: 'Recevoir une copie de vos données par email',
    exporter_btn: 'Exporter',
    supprimer_compte: 'Supprimer mon compte',
    supprimer_desc: 'Action irréversible — supprime toutes vos données',
    supprimer_btn: 'Supprimer',
    support_label: 'Support',
    contacter_support: 'Contacter le support',
    support_desc: 'Nous répondons sous 24h',
    ecrire_btn: '✉️ Écrire',
    mentions_legales: 'Mentions légales',
    confidentialite: 'Politique de confidentialité',
    voir_btn: 'Voir',
    langue_interface: 'Langue de l\'interface',
    langue_desc: 'Changer la langue sur toutes les pages',
    // Connexion
    connexion: 'Connexion',
    identifiants: 'Entrez vos identifiants Aria FORGEDIS',
    google_btn: 'Continuer avec Google',
    email_placeholder: 'votre@email.com',
    mdp_label: 'Mot de passe',
    mdp_oublie: 'Mot de passe oublié ?',
    se_connecter: 'Se connecter →',
    pas_de_compte: 'Pas encore de compte ?',
    sinscrire: 'S\'inscrire',
    pas_abonne: 'Pas encore abonné ?',
    // Modals
    resilier_titre: 'Résilier l\'abonnement',
    resilier_texte: 'Votre abonnement Aria Facility sera annulé à la fin de la période en cours. Vous passerez automatiquement au forfait Découverte.',
    supprimer_titre: 'Supprimer mon compte',
    supprimer_texte: 'Cette action est irréversible. Toutes vos données seront supprimées dans un délai de 30 jours.',
    confirmer: 'Confirmer la résiliation',
    supprimer_confirm: 'Supprimer définitivement',
    annuler: 'Annuler',
    // Accès rapide
    acces_rapide: 'Accès rapide',
    gerer_abonnement: 'Gérer l\'abonnement',
    gerer_sub: 'Changer, résilier, facturation',
    parametres_label: 'Paramètres',
    parametres_sub: 'Email, token, langue',
    support_btn: 'Support',
    support_sub: 'contact@forgedis.fr',
    // Vitrine commune
    essai_gratuit: 'Essai gratuit',
    commencer_essai: 'Commencer l\'essai gratuit →',
    sans_engagement: 'Sans engagement',
    sans_cb: 'Sans carte bancaire',
    resiliable: 'Résiliable à tout moment',
    questions: 'Des questions ?',
    retour_site: '← Retour au site',
  },

  en: {
    ind_deconnexion: 'Sign out',
    ind_poste_dirigeant: 'Director',
    ind_nav_vue_ensemble: 'Overview',
    ind_nav_equipe: 'Team',
    ind_nav_pilotage: 'Finance',
    ind_nav_operations: 'Operations',
    ind_nav_ia: 'AI and Insights',
    ind_nav_config: 'Settings',
    ind_nav_mon_espace: 'My space',
    ind_brand_sub: 'Director',
    ind_tableau_bord: 'Dashboard',
    ind_salaries: 'Employees',
    ind_presences: 'Attendance',
    ind_absences: 'Absences',
    ind_equipes: 'Teams and org chart',
    ind_permissions: 'Employee permissions',
    ind_facturation: 'Invoicing',
    ind_tresorerie: 'Cash flow',
    ind_bc: 'Purchase orders',
    ind_taches: 'Company tasks',
    ind_tickets: 'Customer service',
    ind_stock: 'Stock',
    ind_consulting: 'Aria Consulting',
    ind_reunions: 'Meetings and notes',
    ind_briefing: 'Morning briefing',
    ind_config: 'Company and settings',
    ind_securite: 'Security and access',
    ind_pointage: 'Time tracking',
    ind_mes_conges: 'My leave',
    ind_droits: 'My rights',
    ind_formation: 'Training',
    ind_journal: 'Activity log',
    nav_retour_site: '← Back to site',
    nav_tableau_bord: 'Dashboard',
    nav_abonnement: 'My subscription',
    nav_historique: 'History',
    nav_formation: 'Training',
    nav_fonctionnalites: 'Features',
    nav_parametres: 'Settings',
    nav_support: 'Support',
    nav_deconnexion: 'Sign out',
    nav_compte: 'Main',
    nav_section_compte: 'Account',
    bonjour: 'Hello',
    apercu_mois: 'Here is an overview of your Aria usage this month.',
    eco_taches: 'Eco-tasks used',
    forfait_actuel: 'Current plan',
    statut: 'Status',
    sur_30_mois: 'out of 30 this month',
    acces_illimite: 'Unlimited access',
    abonnement_en_cours: 'Subscription active',
    dl_windows_titre: 'Aria Agent for your computer',
    dl_windows_desc: 'Install the agent on your PC — Aria can open files, browse, reply to emails.',
    dl_windows_btn: '⬇ Download for Windows',
    dl_android_titre: 'Aria App — Android',
    dl_android_desc: 'Talk to Aria from your phone — it sends your requests to the agent on your computer.',
    dl_android_btn: '⬇ Download Android APK',
    dl_iphone_titre: 'Aria App — iPhone',
    dl_iphone_desc: 'The iPhone version of Aria is being reviewed on the Apple App Store.',
    dl_iphone_btn: 'Coming soon',
    mon_abonnement: 'My subscription',
    gerer_forfait: 'Manage your Aria FORGEDIS plan.',
    plan_decouverte: 'Discovery',
    plan_facility: 'Aria Facility',
    actions_illimitees: 'Unlimited actions',
    pilotage_pc: 'Full PC control',
    toutes_langues: 'All languages',
    assistance_prioritaire: 'Priority support',
    donnees_chez_vous: 'Data stays with you',
    bouclier_arnaque: 'Anti-scam shield',
    resilier: 'Cancel subscription',
    passer_facility: '⭐ Upgrade to Aria Facility',
    essai_14j: 'Try 14 days free →',
    historique: 'History',
    activite_recente: 'Recent activity',
    connexion_compte: 'Account login',
    analyse_document: 'Document analysis',
    abonnement_active: 'Subscription activated',
    aujourd_hui: 'Today',
    cette_semaine: 'This week',
    ce_mois: 'This month',
    reussi: 'Success',
    termine: 'Done',
    actif: 'Active',
    parametres: 'Settings',
    infos_compte: 'Account information',
    adresse_email: 'Email address',
    email_desc: 'Used for your subscription and notifications',
    forfait: 'Plan',
    forfait_desc: 'Your current subscription',
    statut_label: 'Status',
    statut_desc: 'Your subscription status',
    eco_ce_mois: 'Eco-tasks this month',
    eco_desc: 'Reset on the 1st of each month',
    securite: 'Security',
    token_aria: 'Aria identifier (token)',
    token_desc: 'Your unique access key — never share it',
    chiffrement: 'Encryption',
    chiffrement_desc: 'Your data is encrypted in transit',
    chiffrement_actif: '✓ Active',
    donnees_rgpd: 'Data & GDPR',
    exporter_donnees: 'Export my data',
    exporter_desc: 'Receive a copy of your data by email',
    exporter_btn: 'Export',
    supprimer_compte: 'Delete my account',
    supprimer_desc: 'Irreversible action — deletes all your data',
    supprimer_btn: 'Delete',
    support_label: 'Support',
    contacter_support: 'Contact support',
    support_desc: 'We reply within 24h',
    ecrire_btn: '✉️ Write',
    mentions_legales: 'Legal notices',
    confidentialite: 'Privacy policy',
    voir_btn: 'View',
    langue_interface: 'Interface language',
    langue_desc: 'Change language across all pages',
    connexion: 'Sign in',
    identifiants: 'Enter your Aria FORGEDIS credentials',
    google_btn: 'Continue with Google',
    email_placeholder: 'your@email.com',
    mdp_label: 'Password',
    mdp_oublie: 'Forgot password?',
    se_connecter: 'Sign in →',
    pas_de_compte: 'No account yet?',
    sinscrire: 'Sign up',
    pas_abonne: 'Not subscribed yet?',
    resilier_titre: 'Cancel subscription',
    resilier_texte: 'Your Aria Facility subscription will be cancelled at the end of the current period. You will automatically move to the Discovery plan.',
    supprimer_titre: 'Delete my account',
    supprimer_texte: 'This action is irreversible. All your data will be deleted within 30 days.',
    confirmer: 'Confirm cancellation',
    supprimer_confirm: 'Delete permanently',
    annuler: 'Cancel',
    acces_rapide: 'Quick access',
    gerer_abonnement: 'Manage subscription',
    gerer_sub: 'Change, cancel, billing',
    parametres_label: 'Settings',
    parametres_sub: 'Email, token, language',
    support_btn: 'Support',
    support_sub: 'contact@forgedis.fr',
    essai_gratuit: 'Free trial',
    commencer_essai: 'Start free trial →',
    sans_engagement: 'No commitment',
    sans_cb: 'No credit card',
    resiliable: 'Cancel anytime',
    questions: 'Questions?',
    retour_site: '← Back to site',
  },

  sa: {
    ind_deconnexion: 'logout',
    ind_poste_dirigeant: 'almudir',
    ind_nav_vue_ensemble: 'nzra 3ama',
    ind_nav_equipe: 'alfariiq',
    ind_nav_pilotage: 'almaliya',
    ind_nav_operations: 'al3mliyat',
    ind_nav_ia: 'aldhaka2',
    ind_nav_config: 'alidadat',
    ind_nav_mon_espace: 'masahty',
    ind_brand_sub: 'mudir',
    ind_tableau_bord: 'lawhat alqiada',
    ind_salaries: 'almuwzfun',
    ind_presences: 'alhudhur',
    ind_absences: 'alghibiyat',
    ind_equipes: 'alfrq walhykl',
    ind_permissions: 'slahiyat almuwzfin',
    ind_facturation: 'alfwatir',
    ind_tresorerie: 'altdafq alnaqdi',
    ind_bc: 'awamir alshira2',
    ind_taches: 'mhm alshrika',
    ind_tickets: 'khidmat al3mlaa2',
    ind_stock: 'almakhzun',
    ind_consulting: 'istisharat aria',
    ind_reunions: 'alijtima3at',
    ind_briefing: 'alihata alsabahiya',
    ind_config: 'alshrika walaadadat',
    ind_securite: 'alamn walwusul',
    ind_pointage: 'tasjil alwaqt',
    ind_mes_conges: 'ijazaty',
    ind_droits: 'huquqi',
    ind_formation: 'altadrib',
    ind_journal: 'sijl alnashat',
    nav_retour_site: '← العودة إلى الموقع',
    nav_tableau_bord: 'لوحة التحكم',
    nav_abonnement: 'اشتراكي',
    nav_historique: 'السجل',
    nav_formation: 'التدريب',
    nav_fonctionnalites: 'الميزات',
    nav_parametres: 'الإعدادات',
    nav_support: 'الدعم',
    nav_deconnexion: 'تسجيل الخروج',
    nav_compte: 'الرئيسية',
    nav_section_compte: 'الحساب',
    bonjour: 'مرحبًا',
    apercu_mois: 'إليك نظرة عامة على استخدامك لـ Aria هذا الشهر.',
    eco_taches: 'المهام المستخدمة',
    forfait_actuel: 'الخطة الحالية',
    statut: 'الحالة',
    sur_30_mois: 'من 30 هذا الشهر',
    acces_illimite: 'وصول غير محدود',
    abonnement_en_cours: 'الاشتراك نشط',
    dl_windows_titre: 'عميل Aria لجهاز الكمبيوتر',
    dl_windows_desc: 'ثبّت العميل على جهازك — يمكن لـ Aria فتح الملفات والتصفح والرد على رسائلك.',
    dl_windows_btn: '⬇ تحميل لـ Windows',
    dl_android_titre: 'تطبيق Aria — Android',
    dl_android_desc: 'تحدّث إلى Aria من هاتفك — ترسل طلباتك إلى العميل على جهازك.',
    dl_android_btn: '⬇ تحميل APK Android',
    dl_iphone_titre: 'تطبيق Aria — iPhone',
    dl_iphone_desc: 'نسخة iPhone من Aria قيد المراجعة على App Store.',
    dl_iphone_btn: 'قريبًا',
    mon_abonnement: 'اشتراكي',
    gerer_forfait: 'إدارة خطة Aria FORGEDIS الخاصة بك.',
    plan_decouverte: 'الاستكشاف',
    plan_facility: 'Aria Facility',
    actions_illimitees: 'إجراءات غير محدودة',
    pilotage_pc: 'تحكم كامل بالكمبيوتر',
    toutes_langues: 'جميع اللغات',
    assistance_prioritaire: 'دعم أولوية',
    donnees_chez_vous: 'بياناتك عندك',
    bouclier_arnaque: 'درع مكافحة الاحتيال',
    resilier: 'إلغاء الاشتراك',
    passer_facility: '⭐ الترقية إلى Aria Facility',
    essai_14j: 'جرّب 14 يومًا مجانًا →',
    historique: 'السجل',
    activite_recente: 'النشاط الأخير',
    connexion_compte: 'تسجيل الدخول',
    analyse_document: 'تحليل المستند',
    abonnement_active: 'تم تفعيل الاشتراك',
    aujourd_hui: 'اليوم',
    cette_semaine: 'هذا الأسبوع',
    ce_mois: 'هذا الشهر',
    reussi: 'ناجح',
    termine: 'منجز',
    actif: 'نشط',
    parametres: 'الإعدادات',
    infos_compte: 'معلومات الحساب',
    adresse_email: 'البريد الإلكتروني',
    email_desc: 'يُستخدم للاشتراك والإشعارات',
    forfait: 'الخطة',
    forfait_desc: 'اشتراكك الحالي',
    statut_label: 'الحالة',
    statut_desc: 'حالة اشتراكك',
    eco_ce_mois: 'المهام هذا الشهر',
    eco_desc: 'تُعاد في الأول من كل شهر',
    securite: 'الأمان',
    token_aria: 'معرّف Aria',
    token_desc: 'مفتاح وصولك الفريد — لا تشاركه أبدًا',
    chiffrement: 'التشفير',
    chiffrement_desc: 'بياناتك مشفّرة أثناء النقل',
    chiffrement_actif: '✓ نشط',
    donnees_rgpd: 'البيانات والخصوصية',
    exporter_donnees: 'تصدير بياناتي',
    exporter_desc: 'استلام نسخة من بياناتك عبر البريد',
    exporter_btn: 'تصدير',
    supprimer_compte: 'حذف حسابي',
    supprimer_desc: 'إجراء لا رجعة فيه — يحذف جميع بياناتك',
    supprimer_btn: 'حذف',
    support_label: 'الدعم',
    contacter_support: 'التواصل مع الدعم',
    support_desc: 'نردّ خلال 24 ساعة',
    ecrire_btn: '✉️ كتابة',
    mentions_legales: 'الإشعارات القانونية',
    confidentialite: 'سياسة الخصوصية',
    voir_btn: 'عرض',
    langue_interface: 'لغة الواجهة',
    langue_desc: 'تغيير اللغة في جميع الصفحات',
    connexion: 'تسجيل الدخول',
    identifiants: 'أدخل بيانات Aria FORGEDIS الخاصة بك',
    google_btn: 'المتابعة مع Google',
    email_placeholder: 'بريدك@الإلكتروني.com',
    mdp_label: 'كلمة المرور',
    mdp_oublie: 'نسيت كلمة المرور؟',
    se_connecter: 'تسجيل الدخول →',
    pas_de_compte: 'ليس لديك حساب؟',
    sinscrire: 'إنشاء حساب',
    pas_abonne: 'لم تشترك بعد؟',
    resilier_titre: 'إلغاء الاشتراك',
    resilier_texte: 'سيتم إلغاء اشتراكك في Aria Facility في نهاية الفترة الحالية.',
    supprimer_titre: 'حذف حسابي',
    supprimer_texte: 'هذا الإجراء لا رجعة فيه. ستُحذف جميع بياناتك خلال 30 يومًا.',
    confirmer: 'تأكيد الإلغاء',
    supprimer_confirm: 'حذف نهائي',
    annuler: 'إلغاء',
    acces_rapide: 'وصول سريع',
    gerer_abonnement: 'إدارة الاشتراك',
    gerer_sub: 'تغيير، إلغاء، فوترة',
    parametres_label: 'الإعدادات',
    parametres_sub: 'البريد، المعرّف، اللغة',
    support_btn: 'الدعم',
    support_sub: 'contact@forgedis.fr',
    essai_gratuit: 'تجربة مجانية',
    commencer_essai: 'ابدأ التجربة المجانية →',
    sans_engagement: 'بدون التزام',
    sans_cb: 'بدون بطاقة بنكية',
    resiliable: 'إلغاء في أي وقت',
    questions: 'أسئلة؟',
    retour_site: '← العودة إلى الموقع',
  },

  dz: {
    ind_deconnexion: 'khuruj',
    ind_poste_dirigeant: 'almudir',
    ind_nav_vue_ensemble: 'nzra 3ama',
    ind_nav_equipe: 'alfariiq',
    ind_nav_pilotage: 'almaliya',
    ind_nav_operations: 'al3mliyat',
    ind_nav_ia: 'aldhaka2',
    ind_nav_config: 'alidadat',
    ind_nav_mon_espace: 'masahty',
    ind_brand_sub: 'mudir',
    ind_tableau_bord: 'lawhat alqiada',
    ind_salaries: 'almuwzfin',
    ind_presences: 'alhudhur',
    ind_absences: 'alghibiyat',
    ind_equipes: 'alfrq walhykl attanzimi',
    ind_permissions: 'slahiyat almuwzfin',
    ind_facturation: 'alfwatir',
    ind_tresorerie: 'alkhazina',
    ind_bc: 'talabat alshira2',
    ind_taches: 'mhm alshrika',
    ind_tickets: 'khidmat al3mlaa2',
    ind_stock: 'almakhzun',
    ind_consulting: 'istisharat aria',
    ind_reunions: 'alijtima3at',
    ind_briefing: 'alihata alsabahiya',
    ind_config: 'alshrika walaadadat',
    ind_securite: 'alamn walwusul',
    ind_pointage: 'tasjil alwaqt',
    ind_mes_conges: 'ijazaty',
    ind_droits: 'huquqi',
    ind_formation: 'attakwin',
    ind_journal: 'sijl alnashat',
    nav_retour_site: '← ارجع للموقع',
    nav_tableau_bord: 'لوحة التحكم',
    nav_abonnement: 'اشتراكي',
    nav_historique: 'السجل',
    nav_formation: 'التكوين',
    nav_fonctionnalites: 'الميزات',
    nav_parametres: 'الإعدادات',
    nav_support: 'المساعدة',
    nav_deconnexion: 'خروج',
    nav_compte: 'الرئيسية',
    nav_section_compte: 'الحساب',
    bonjour: 'أهلا',
    apercu_mois: 'شوف كيفاش خدمت مع Aria هذ الشهر.',
    eco_taches: 'المهام المستعملة',
    forfait_actuel: 'الفورفي الحالي',
    statut: 'الحالة',
    sur_30_mois: 'من 30 هذ الشهر',
    acces_illimite: 'وصول بلا حدود',
    abonnement_en_cours: 'الاشتراك شغّال',
    dl_windows_titre: 'عميل Aria للكمبيوتر',
    dl_windows_desc: 'ثبّت العميل على PC تاعك — Aria تفتحلك الملفات وتتصفح وترد على الإيميلات.',
    dl_windows_btn: '⬇ حمّل لـ Windows',
    dl_android_titre: 'تطبيق Aria — Android',
    dl_android_desc: 'حكيلـ Aria من التيليفون تاعك — تبعت الطلبات للـ PC.',
    dl_android_btn: '⬇ حمّل APK Android',
    dl_iphone_titre: 'تطبيق Aria — iPhone',
    dl_iphone_desc: 'نسخة iPhone تاع Aria راها في المراجعة على App Store.',
    dl_iphone_btn: 'قريبًا',
    mon_abonnement: 'اشتراكي',
    gerer_forfait: 'دير الفورفي تاع Aria FORGEDIS.',
    plan_decouverte: 'اكتشاف',
    plan_facility: 'Aria Facility',
    actions_illimitees: 'أعمال بلا حدود',
    pilotage_pc: 'تحكم كامل بالـ PC',
    toutes_langues: 'كل اللغات',
    assistance_prioritaire: 'مساعدة أولوية',
    donnees_chez_vous: 'معطياتك عندك',
    bouclier_arnaque: 'حماية من النصب',
    resilier: 'ألغي الاشتراك',
    passer_facility: '⭐ روح لـ Aria Facility',
    essai_14j: 'جرّب 14 يوم مجانًا →',
    historique: 'السجل',
    activite_recente: 'النشاط الأخير',
    connexion_compte: 'دخول للحساب',
    analyse_document: 'تحليل الوثيقة',
    abonnement_active: 'تفعّل الاشتراك',
    aujourd_hui: 'اليوم',
    cette_semaine: 'هذ الأسبوع',
    ce_mois: 'هذ الشهر',
    reussi: 'نجح',
    termine: 'خلاص',
    actif: 'شغّال',
    parametres: 'الإعدادات',
    infos_compte: 'معلومات الحساب',
    adresse_email: 'الإيميل',
    email_desc: 'يُستعمل للاشتراك والإشعارات',
    forfait: 'الفورفي',
    forfait_desc: 'الاشتراك الحالي تاعك',
    statut_label: 'الحالة',
    statut_desc: 'حالة الاشتراك تاعك',
    eco_ce_mois: 'المهام هذ الشهر',
    eco_desc: 'يتصفّر في أول كل شهر',
    securite: 'الأمان',
    token_aria: 'معرّف Aria',
    token_desc: 'مفتاح الوصول تاعك — ما تشاركوش',
    chiffrement: 'التشفير',
    chiffrement_desc: 'معطياتك مشفّرة وقت النقل',
    chiffrement_actif: '✓ شغّال',
    donnees_rgpd: 'المعطيات والخصوصية',
    exporter_donnees: 'صدّر معطياتي',
    exporter_desc: 'استلم نسخة من معطياتك بالإيميل',
    exporter_btn: 'تصدير',
    supprimer_compte: 'احذف حسابي',
    supprimer_desc: 'ما تنجمش ترجع — يحذف كل المعطيات تاعك',
    supprimer_btn: 'حذف',
    support_label: 'المساعدة',
    contacter_support: 'تواصل مع الدعم',
    support_desc: 'نردّو خلال 24 ساعة',
    ecrire_btn: '✉️ اكتب',
    mentions_legales: 'الإشعارات القانونية',
    confidentialite: 'سياسة الخصوصية',
    voir_btn: 'شوف',
    langue_interface: 'لغة الواجهة',
    langue_desc: 'بدّل اللغة في كل الصفحات',
    connexion: 'دخول',
    identifiants: 'دخّل بيانات Aria FORGEDIS تاعك',
    google_btn: 'كمّل مع Google',
    email_placeholder: 'إيميلك@هنا.com',
    mdp_label: 'كلمة السر',
    mdp_oublie: 'نسيت كلمة السر؟',
    se_connecter: 'دخول →',
    pas_de_compte: 'ما عندكش حساب؟',
    sinscrire: 'سجّل',
    pas_abonne: 'ما اشتركتش بعد؟',
    resilier_titre: 'ألغي الاشتراك',
    resilier_texte: 'يتألغى اشتراكك في Aria Facility في آخر الفترة الحالية.',
    supprimer_titre: 'احذف حسابي',
    supprimer_texte: 'ما تنجمش ترجع. تتحذف كل المعطيات خلال 30 يوم.',
    confirmer: 'أكّد الإلغاء',
    supprimer_confirm: 'حذف نهائي',
    annuler: 'إلغاء',
    acces_rapide: 'وصول سريع',
    gerer_abonnement: 'دير الاشتراك',
    gerer_sub: 'بدّل، ألغي، فوترة',
    parametres_label: 'الإعدادات',
    parametres_sub: 'الإيميل، المعرّف، اللغة',
    support_btn: 'المساعدة',
    support_sub: 'contact@forgedis.fr',
    essai_gratuit: 'تجربة مجانية',
    commencer_essai: 'ابدأ التجربة المجانية →',
    sans_engagement: 'بلا التزام',
    sans_cb: 'بلا بطاقة',
    resiliable: 'ألغي وقتاش تحب',
    questions: 'أسئلة؟',
    retour_site: '← ارجع للموقع',
  },

  es: {
    ind_deconnexion: 'Cerrar sesion',
    ind_poste_dirigeant: 'Director',
    ind_nav_vue_ensemble: 'Resumen',
    ind_nav_equipe: 'Equipo',
    ind_nav_pilotage: 'Finanzas',
    ind_nav_operations: 'Operaciones',
    ind_nav_ia: 'IA y Analisis',
    ind_nav_config: 'Configuracion',
    ind_nav_mon_espace: 'Mi espacio',
    ind_brand_sub: 'Director',
    ind_tableau_bord: 'Panel',
    ind_salaries: 'Empleados',
    ind_presences: 'Asistencia',
    ind_absences: 'Ausencias',
    ind_equipes: 'Equipos y organigrama',
    ind_permissions: 'Permisos empleados',
    ind_facturation: 'Facturacion',
    ind_tresorerie: 'Tesoreria',
    ind_bc: 'Pedidos de compra',
    ind_taches: 'Tareas empresa',
    ind_tickets: 'Atencion al cliente',
    ind_stock: 'Stock',
    ind_consulting: 'Aria Consulting',
    ind_reunions: 'Reuniones y actas',
    ind_briefing: 'Briefing matutino',
    ind_config: 'Empresa y config',
    ind_securite: 'Seguridad y acceso',
    ind_pointage: 'Control horario',
    ind_mes_conges: 'Mis vacaciones',
    ind_droits: 'Mis derechos',
    ind_formation: 'Formacion',
    ind_journal: 'Registro de actividad',
    nav_retour_site: '← Volver al sitio',
    nav_tableau_bord: 'Panel de control',
    nav_abonnement: 'Mi suscripción',
    nav_historique: 'Historial',
    nav_formation: 'Formación',
    nav_fonctionnalites: 'Funciones',
    nav_parametres: 'Ajustes',
    nav_support: 'Soporte',
    nav_deconnexion: 'Cerrar sesión',
    nav_compte: 'Principal',
    nav_section_compte: 'Cuenta',
    bonjour: 'Hola',
    apercu_mois: 'Aquí tienes un resumen de tu uso de Aria este mes.',
    eco_taches: 'Eco-tareas usadas',
    forfait_actuel: 'Plan actual',
    statut: 'Estado',
    sur_30_mois: 'de 30 este mes',
    acces_illimite: 'Acceso ilimitado',
    abonnement_en_cours: 'Suscripción activa',
    dl_windows_titre: 'Agente Aria para tu ordenador',
    dl_windows_desc: 'Instala el agente en tu PC — Aria puede abrir archivos, navegar, responder emails.',
    dl_windows_btn: '⬇ Descargar para Windows',
    dl_android_titre: 'App Aria — Android',
    dl_android_desc: 'Habla con Aria desde tu teléfono — envía tus solicitudes al agente en tu PC.',
    dl_android_btn: '⬇ Descargar APK Android',
    dl_iphone_titre: 'App Aria — iPhone',
    dl_iphone_desc: 'La versión iPhone de Aria está siendo revisada en el App Store de Apple.',
    dl_iphone_btn: 'Próximamente',
    mon_abonnement: 'Mi suscripción',
    gerer_forfait: 'Gestiona tu plan Aria FORGEDIS.',
    plan_decouverte: 'Descubrimiento',
    plan_facility: 'Aria Facility',
    actions_illimitees: 'Acciones ilimitadas',
    pilotage_pc: 'Control total del PC',
    toutes_langues: 'Todos los idiomas',
    assistance_prioritaire: 'Soporte prioritario',
    donnees_chez_vous: 'Datos en tu dispositivo',
    bouclier_arnaque: 'Escudo anti-estafa',
    resilier: 'Cancelar suscripción',
    passer_facility: '⭐ Pasar a Aria Facility',
    essai_14j: 'Prueba 14 días gratis →',
    historique: 'Historial',
    activite_recente: 'Actividad reciente',
    connexion_compte: 'Inicio de sesión',
    analyse_document: 'Análisis de documento',
    abonnement_active: 'Suscripción activada',
    aujourd_hui: 'Hoy',
    cette_semaine: 'Esta semana',
    ce_mois: 'Este mes',
    reussi: 'Éxito',
    termine: 'Completado',
    actif: 'Activo',
    parametres: 'Ajustes',
    infos_compte: 'Información de la cuenta',
    adresse_email: 'Correo electrónico',
    email_desc: 'Usado para tu suscripción y notificaciones',
    forfait: 'Plan',
    forfait_desc: 'Tu suscripción actual',
    statut_label: 'Estado',
    statut_desc: 'Estado de tu suscripción',
    eco_ce_mois: 'Eco-tareas este mes',
    eco_desc: 'Se reinicia el 1 de cada mes',
    securite: 'Seguridad',
    token_aria: 'Identificador Aria (token)',
    token_desc: 'Tu clave de acceso única — nunca la compartas',
    chiffrement: 'Cifrado',
    chiffrement_desc: 'Tus datos están cifrados en tránsito',
    chiffrement_actif: '✓ Activo',
    donnees_rgpd: 'Datos y privacidad',
    exporter_donnees: 'Exportar mis datos',
    exporter_desc: 'Recibe una copia de tus datos por email',
    exporter_btn: 'Exportar',
    supprimer_compte: 'Eliminar mi cuenta',
    supprimer_desc: 'Acción irreversible — elimina todos tus datos',
    supprimer_btn: 'Eliminar',
    support_label: 'Soporte',
    contacter_support: 'Contactar soporte',
    support_desc: 'Respondemos en 24h',
    ecrire_btn: '✉️ Escribir',
    mentions_legales: 'Aviso legal',
    confidentialite: 'Política de privacidad',
    voir_btn: 'Ver',
    langue_interface: 'Idioma de la interfaz',
    langue_desc: 'Cambiar idioma en todas las páginas',
    connexion: 'Iniciar sesión',
    identifiants: 'Introduce tus credenciales de Aria FORGEDIS',
    google_btn: 'Continuar con Google',
    email_placeholder: 'tu@email.com',
    mdp_label: 'Contraseña',
    mdp_oublie: '¿Olvidaste tu contraseña?',
    se_connecter: 'Iniciar sesión →',
    pas_de_compte: '¿Aún no tienes cuenta?',
    sinscrire: 'Registrarse',
    pas_abonne: '¿Aún no estás suscrito?',
    resilier_titre: 'Cancelar suscripción',
    resilier_texte: 'Tu suscripción a Aria Facility se cancelará al final del período actual.',
    supprimer_titre: 'Eliminar mi cuenta',
    supprimer_texte: 'Esta acción es irreversible. Todos tus datos serán eliminados en 30 días.',
    confirmer: 'Confirmar cancelación',
    supprimer_confirm: 'Eliminar definitivamente',
    annuler: 'Cancelar',
    acces_rapide: 'Acceso rápido',
    gerer_abonnement: 'Gestionar suscripción',
    gerer_sub: 'Cambiar, cancelar, facturación',
    parametres_label: 'Ajustes',
    parametres_sub: 'Email, token, idioma',
    support_btn: 'Soporte',
    support_sub: 'contact@forgedis.fr',
    essai_gratuit: 'Prueba gratuita',
    commencer_essai: 'Iniciar prueba gratuita →',
    sans_engagement: 'Sin compromiso',
    sans_cb: 'Sin tarjeta de crédito',
    resiliable: 'Cancela cuando quieras',
    questions: '¿Preguntas?',
    retour_site: '← Volver al sitio',
  },

  pt: {
    ind_deconnexion: 'Sair',
    ind_poste_dirigeant: 'Diretor',
    ind_nav_vue_ensemble: 'Visao geral',
    ind_nav_equipe: 'Equipe',
    ind_nav_pilotage: 'Financas',
    ind_nav_operations: 'Operacoes',
    ind_nav_ia: 'IA e Analise',
    ind_nav_config: 'Configuracoes',
    ind_nav_mon_espace: 'Meu espaco',
    ind_brand_sub: 'Diretor',
    ind_tableau_bord: 'Painel',
    ind_salaries: 'Funcionarios',
    ind_presences: 'Presenca',
    ind_absences: 'Ausencias',
    ind_equipes: 'Equipes e organograma',
    ind_permissions: 'Permissoes',
    ind_facturation: 'Faturamento',
    ind_tresorerie: 'Tesouraria',
    ind_bc: 'Pedidos de compra',
    ind_taches: 'Tarefas empresa',
    ind_tickets: 'Atendimento ao cliente',
    ind_stock: 'Estoque',
    ind_consulting: 'Aria Consulting',
    ind_reunions: 'Reunioes e atas',
    ind_briefing: 'Briefing matinal',
    ind_config: 'Empresa e config',
    ind_securite: 'Seguranca e acesso',
    ind_pointage: 'Registro de ponto',
    ind_mes_conges: 'Minhas ferias',
    ind_droits: 'Meus direitos',
    ind_formation: 'Formacao',
    ind_journal: 'Registro de atividade',
    nav_retour_site: '← Voltar ao site',
    nav_tableau_bord: 'Painel de controlo',
    nav_abonnement: 'Minha assinatura',
    nav_historique: 'Histórico',
    nav_formation: 'Formação',
    nav_fonctionnalites: 'Funcionalidades',
    nav_parametres: 'Definições',
    nav_support: 'Suporte',
    nav_deconnexion: 'Terminar sessão',
    nav_compte: 'Principal',
    nav_section_compte: 'Conta',
    bonjour: 'Olá',
    apercu_mois: 'Aqui está uma visão geral do seu uso do Aria este mês.',
    eco_taches: 'Eco-tarefas utilizadas',
    forfait_actuel: 'Plano atual',
    statut: 'Estado',
    sur_30_mois: 'de 30 este mês',
    acces_illimite: 'Acesso ilimitado',
    abonnement_en_cours: 'Assinatura ativa',
    dl_windows_titre: 'Agente Aria para o seu computador',
    dl_windows_desc: 'Instale o agente no seu PC — Aria pode abrir ficheiros, navegar, responder emails.',
    dl_windows_btn: '⬇ Descarregar para Windows',
    dl_android_titre: 'App Aria — Android',
    dl_android_desc: 'Fale com Aria a partir do seu telemóvel — envia os seus pedidos ao agente no PC.',
    dl_android_btn: '⬇ Descarregar APK Android',
    dl_iphone_titre: 'App Aria — iPhone',
    dl_iphone_desc: 'A versão iPhone do Aria está a ser analisada na App Store da Apple.',
    dl_iphone_btn: 'Em breve',
    mon_abonnement: 'Minha assinatura',
    gerer_forfait: 'Gerir o seu plano Aria FORGEDIS.',
    plan_decouverte: 'Descoberta',
    plan_facility: 'Aria Facility',
    actions_illimitees: 'Ações ilimitadas',
    pilotage_pc: 'Controlo total do PC',
    toutes_langues: 'Todos os idiomas',
    assistance_prioritaire: 'Suporte prioritário',
    donnees_chez_vous: 'Dados no seu dispositivo',
    bouclier_arnaque: 'Escudo anti-fraude',
    resilier: 'Cancelar assinatura',
    passer_facility: '⭐ Passar para Aria Facility',
    essai_14j: 'Experimente 14 dias grátis →',
    historique: 'Histórico',
    activite_recente: 'Atividade recente',
    connexion_compte: 'Início de sessão',
    analyse_document: 'Análise de documento',
    abonnement_active: 'Assinatura ativada',
    aujourd_hui: 'Hoje',
    cette_semaine: 'Esta semana',
    ce_mois: 'Este mês',
    reussi: 'Sucesso',
    termine: 'Concluído',
    actif: 'Ativo',
    parametres: 'Definições',
    infos_compte: 'Informações da conta',
    adresse_email: 'Endereço de email',
    email_desc: 'Utilizado para a sua assinatura e notificações',
    forfait: 'Plano',
    forfait_desc: 'A sua assinatura atual',
    statut_label: 'Estado',
    statut_desc: 'Estado da sua assinatura',
    eco_ce_mois: 'Eco-tarefas este mês',
    eco_desc: 'Reinicia no dia 1 de cada mês',
    securite: 'Segurança',
    token_aria: 'Identificador Aria (token)',
    token_desc: 'A sua chave de acesso única — nunca partilhe',
    chiffrement: 'Encriptação',
    chiffrement_desc: 'Os seus dados são encriptados em trânsito',
    chiffrement_actif: '✓ Ativo',
    donnees_rgpd: 'Dados e privacidade',
    exporter_donnees: 'Exportar os meus dados',
    exporter_desc: 'Receber uma cópia dos seus dados por email',
    exporter_btn: 'Exportar',
    supprimer_compte: 'Eliminar a minha conta',
    supprimer_desc: 'Ação irreversível — elimina todos os seus dados',
    supprimer_btn: 'Eliminar',
    support_label: 'Suporte',
    contacter_support: 'Contactar suporte',
    support_desc: 'Respondemos em 24h',
    ecrire_btn: '✉️ Escrever',
    mentions_legales: 'Avisos legais',
    confidentialite: 'Política de privacidade',
    voir_btn: 'Ver',
    langue_interface: 'Idioma da interface',
    langue_desc: 'Alterar idioma em todas as páginas',
    connexion: 'Iniciar sessão',
    identifiants: 'Introduza as suas credenciais Aria FORGEDIS',
    google_btn: 'Continuar com Google',
    email_placeholder: 'o-seu@email.com',
    mdp_label: 'Palavra-passe',
    mdp_oublie: 'Esqueceu a palavra-passe?',
    se_connecter: 'Iniciar sessão →',
    pas_de_compte: 'Ainda não tem conta?',
    sinscrire: 'Registar',
    pas_abonne: 'Ainda não está subscrito?',
    resilier_titre: 'Cancelar assinatura',
    resilier_texte: 'A sua assinatura Aria Facility será cancelada no final do período atual.',
    supprimer_titre: 'Eliminar a minha conta',
    supprimer_texte: 'Esta ação é irreversível. Todos os seus dados serão eliminados em 30 dias.',
    confirmer: 'Confirmar cancelamento',
    supprimer_confirm: 'Eliminar definitivamente',
    annuler: 'Cancelar',
    acces_rapide: 'Acesso rápido',
    gerer_abonnement: 'Gerir assinatura',
    gerer_sub: 'Alterar, cancelar, faturação',
    parametres_label: 'Definições',
    parametres_sub: 'Email, token, idioma',
    support_btn: 'Suporte',
    support_sub: 'contact@forgedis.fr',
    essai_gratuit: 'Teste gratuito',
    commencer_essai: 'Iniciar teste gratuito →',
    sans_engagement: 'Sem compromisso',
    sans_cb: 'Sem cartão de crédito',
    resiliable: 'Cancele quando quiser',
    questions: 'Dúvidas?',
    retour_site: '← Voltar ao site',
  },

  de: {
    ind_deconnexion: 'Abmelden',
    ind_poste_dirigeant: 'Direktor',
    ind_nav_vue_ensemble: 'Ubersicht',
    ind_nav_equipe: 'Team',
    ind_nav_pilotage: 'Finanzen',
    ind_nav_operations: 'Betrieb',
    ind_nav_ia: 'KI und Analysen',
    ind_nav_config: 'Einstellungen',
    ind_nav_mon_espace: 'Mein Bereich',
    ind_brand_sub: 'Direktor',
    ind_tableau_bord: 'Dashboard',
    ind_salaries: 'Mitarbeiter',
    ind_presences: 'Anwesenheit',
    ind_absences: 'Abwesenheiten',
    ind_equipes: 'Teams und Organigramm',
    ind_permissions: 'Mitarbeiterrechte',
    ind_facturation: 'Rechnungstellung',
    ind_tresorerie: 'Liquiditat',
    ind_bc: 'Bestellungen',
    ind_taches: 'Unternehmensaufgaben',
    ind_tickets: 'Kundendienst',
    ind_stock: 'Lager',
    ind_consulting: 'Aria Consulting',
    ind_reunions: 'Besprechungen und Protokolle',
    ind_briefing: 'Morgenbriefing',
    ind_config: 'Unternehmen und Einstellungen',
    ind_securite: 'Sicherheit und Zugang',
    ind_pointage: 'Zeiterfassung',
    ind_mes_conges: 'Mein Urlaub',
    ind_droits: 'Meine Rechte',
    ind_formation: 'Weiterbildung',
    ind_journal: 'Aktivitatsprotokoll',
    nav_retour_site: '← Zurück zur Website',
    nav_tableau_bord: 'Dashboard',
    nav_abonnement: 'Mein Abonnement',
    nav_historique: 'Verlauf',
    nav_formation: 'Training',
    nav_fonctionnalites: 'Funktionen',
    nav_parametres: 'Einstellungen',
    nav_support: 'Support',
    nav_deconnexion: 'Abmelden',
    nav_compte: 'Hauptmenü',
    nav_section_compte: 'Konto',
    bonjour: 'Hallo',
    apercu_mois: 'Hier ist eine Übersicht Ihrer Aria-Nutzung diesen Monat.',
    eco_taches: 'Verwendete Öko-Aufgaben',
    forfait_actuel: 'Aktueller Plan',
    statut: 'Status',
    sur_30_mois: 'von 30 diesen Monat',
    acces_illimite: 'Unbegrenzter Zugang',
    abonnement_en_cours: 'Abonnement aktiv',
    dl_windows_titre: 'Aria-Agent für Ihren Computer',
    dl_windows_desc: 'Installieren Sie den Agenten auf Ihrem PC — Aria kann Dateien öffnen, surfen, E-Mails beantworten.',
    dl_windows_btn: '⬇ Für Windows herunterladen',
    dl_android_titre: 'Aria App — Android',
    dl_android_desc: 'Sprechen Sie mit Aria von Ihrem Telefon — sendet Anfragen an den Agenten auf Ihrem PC.',
    dl_android_btn: '⬇ Android APK herunterladen',
    dl_iphone_titre: 'Aria App — iPhone',
    dl_iphone_desc: 'Die iPhone-Version von Aria wird im Apple App Store überprüft.',
    dl_iphone_btn: 'Demnächst verfügbar',
    mon_abonnement: 'Mein Abonnement',
    gerer_forfait: 'Verwalten Sie Ihren Aria FORGEDIS-Plan.',
    plan_decouverte: 'Entdeckung',
    plan_facility: 'Aria Facility',
    actions_illimitees: 'Unbegrenzte Aktionen',
    pilotage_pc: 'Vollständige PC-Steuerung',
    toutes_langues: 'Alle Sprachen',
    assistance_prioritaire: 'Prioritätssupport',
    donnees_chez_vous: 'Daten auf Ihrem Gerät',
    bouclier_arnaque: 'Anti-Betrugs-Schutzschild',
    resilier: 'Abonnement kündigen',
    passer_facility: '⭐ Zu Aria Facility wechseln',
    essai_14j: '14 Tage kostenlos testen →',
    historique: 'Verlauf',
    activite_recente: 'Letzte Aktivität',
    connexion_compte: 'Kontoanmeldung',
    analyse_document: 'Dokumentenanalyse',
    abonnement_active: 'Abonnement aktiviert',
    aujourd_hui: 'Heute',
    cette_semaine: 'Diese Woche',
    ce_mois: 'Diesen Monat',
    reussi: 'Erfolgreich',
    termine: 'Fertig',
    actif: 'Aktiv',
    parametres: 'Einstellungen',
    infos_compte: 'Kontoinformationen',
    adresse_email: 'E-Mail-Adresse',
    email_desc: 'Für Ihr Abonnement und Benachrichtigungen verwendet',
    forfait: 'Plan',
    forfait_desc: 'Ihr aktuelles Abonnement',
    statut_label: 'Status',
    statut_desc: 'Status Ihres Abonnements',
    eco_ce_mois: 'Öko-Aufgaben diesen Monat',
    eco_desc: 'Wird am 1. jeden Monats zurückgesetzt',
    securite: 'Sicherheit',
    token_aria: 'Aria-Kennung (Token)',
    token_desc: 'Ihr einzigartiger Zugriffsschlüssel — niemals teilen',
    chiffrement: 'Verschlüsselung',
    chiffrement_desc: 'Ihre Daten sind während der Übertragung verschlüsselt',
    chiffrement_actif: '✓ Aktiv',
    donnees_rgpd: 'Daten & Datenschutz',
    exporter_donnees: 'Meine Daten exportieren',
    exporter_desc: 'Eine Kopie Ihrer Daten per E-Mail erhalten',
    exporter_btn: 'Exportieren',
    supprimer_compte: 'Mein Konto löschen',
    supprimer_desc: 'Unwiderrufliche Aktion — löscht alle Ihre Daten',
    supprimer_btn: 'Löschen',
    support_label: 'Support',
    contacter_support: 'Support kontaktieren',
    support_desc: 'Wir antworten innerhalb von 24h',
    ecrire_btn: '✉️ Schreiben',
    mentions_legales: 'Rechtliche Hinweise',
    confidentialite: 'Datenschutzrichtlinie',
    voir_btn: 'Ansehen',
    langue_interface: 'Schnittstellensprache',
    langue_desc: 'Sprache auf allen Seiten ändern',
    connexion: 'Anmelden',
    identifiants: 'Geben Sie Ihre Aria FORGEDIS-Anmeldedaten ein',
    google_btn: 'Mit Google fortfahren',
    email_placeholder: 'ihre@email.com',
    mdp_label: 'Passwort',
    mdp_oublie: 'Passwort vergessen?',
    se_connecter: 'Anmelden →',
    pas_de_compte: 'Noch kein Konto?',
    sinscrire: 'Registrieren',
    pas_abonne: 'Noch nicht abonniert?',
    resilier_titre: 'Abonnement kündigen',
    resilier_texte: 'Ihr Aria Facility-Abonnement wird am Ende der aktuellen Periode gekündigt.',
    supprimer_titre: 'Mein Konto löschen',
    supprimer_texte: 'Diese Aktion ist unwiderruflich. Alle Ihre Daten werden innerhalb von 30 Tagen gelöscht.',
    confirmer: 'Kündigung bestätigen',
    supprimer_confirm: 'Endgültig löschen',
    annuler: 'Abbrechen',
    acces_rapide: 'Schnellzugriff',
    gerer_abonnement: 'Abonnement verwalten',
    gerer_sub: 'Ändern, kündigen, Abrechnung',
    parametres_label: 'Einstellungen',
    parametres_sub: 'E-Mail, Token, Sprache',
    support_btn: 'Support',
    support_sub: 'contact@forgedis.fr',
    essai_gratuit: 'Kostenloser Test',
    commencer_essai: 'Kostenlosen Test starten →',
    sans_engagement: 'Ohne Verpflichtung',
    sans_cb: 'Ohne Kreditkarte',
    resiliable: 'Jederzeit kündbar',
    questions: 'Fragen?',
    retour_site: '← Zurück zur Website',
  },

  it: {
    ind_deconnexion: 'Disconnetti',
    ind_poste_dirigeant: 'Direttore',
    ind_nav_vue_ensemble: 'Panoramica',
    ind_nav_equipe: 'Team',
    ind_nav_pilotage: 'Finanza',
    ind_nav_operations: 'Operazioni',
    ind_nav_ia: 'IA e Analisi',
    ind_nav_config: 'Impostazioni',
    ind_nav_mon_espace: 'Il mio spazio',
    ind_brand_sub: 'Direttore',
    ind_tableau_bord: 'Cruscotto',
    ind_salaries: 'Dipendenti',
    ind_presences: 'Presenze',
    ind_absences: 'Assenze',
    ind_equipes: 'Team e organigramma',
    ind_permissions: 'Permessi dipendenti',
    ind_facturation: 'Fatturazione',
    ind_tresorerie: 'Tesoreria',
    ind_bc: 'Ordini di acquisto',
    ind_taches: 'Attivita aziendali',
    ind_tickets: 'Servizio clienti',
    ind_stock: 'Magazzino',
    ind_consulting: 'Aria Consulting',
    ind_reunions: 'Riunioni e verbali',
    ind_briefing: 'Briefing mattutino',
    ind_config: 'Azienda e config',
    ind_securite: 'Sicurezza e accesso',
    ind_pointage: 'Rilevazione presenze',
    ind_mes_conges: 'Le mie ferie',
    ind_droits: 'I miei diritti',
    ind_formation: 'Formazione',
    ind_journal: 'Registro attivita',
    nav_retour_site: '← Torna al sito',
    nav_tableau_bord: 'Dashboard',
    nav_abonnement: 'Il mio abbonamento',
    nav_historique: 'Cronologia',
    nav_formation: 'Formazione',
    nav_fonctionnalites: 'Funzionalità',
    nav_parametres: 'Impostazioni',
    nav_support: 'Supporto',
    nav_deconnexion: 'Disconnettersi',
    nav_compte: 'Principale',
    nav_section_compte: 'Account',
    bonjour: 'Ciao',
    apercu_mois: 'Ecco una panoramica del tuo utilizzo di Aria questo mese.',
    eco_taches: 'Eco-attività utilizzate',
    forfait_actuel: 'Piano attuale',
    statut: 'Stato',
    sur_30_mois: 'su 30 questo mese',
    acces_illimite: 'Accesso illimitato',
    abonnement_en_cours: 'Abbonamento attivo',
    dl_windows_titre: 'Agente Aria per il tuo computer',
    dl_windows_desc: 'Installa l\'agente sul tuo PC — Aria può aprire file, navigare, rispondere alle email.',
    dl_windows_btn: '⬇ Scarica per Windows',
    dl_android_titre: 'App Aria — Android',
    dl_android_desc: 'Parla con Aria dal tuo telefono — invia le tue richieste all\'agente sul PC.',
    dl_android_btn: '⬇ Scarica APK Android',
    dl_iphone_titre: 'App Aria — iPhone',
    dl_iphone_desc: 'La versione iPhone di Aria è in revisione sull\'App Store di Apple.',
    dl_iphone_btn: 'Prossimamente',
    mon_abonnement: 'Il mio abbonamento',
    gerer_forfait: 'Gestisci il tuo piano Aria FORGEDIS.',
    plan_decouverte: 'Scoperta',
    plan_facility: 'Aria Facility',
    actions_illimitees: 'Azioni illimitate',
    pilotage_pc: 'Controllo completo del PC',
    toutes_langues: 'Tutte le lingue',
    assistance_prioritaire: 'Supporto prioritario',
    donnees_chez_vous: 'Dati sul tuo dispositivo',
    bouclier_arnaque: 'Scudo anti-truffa',
    resilier: 'Annullare l\'abbonamento',
    passer_facility: '⭐ Passa a Aria Facility',
    essai_14j: 'Prova 14 giorni gratis →',
    historique: 'Cronologia',
    activite_recente: 'Attività recente',
    connexion_compte: 'Accesso account',
    analyse_document: 'Analisi documento',
    abonnement_active: 'Abbonamento attivato',
    aujourd_hui: 'Oggi',
    cette_semaine: 'Questa settimana',
    ce_mois: 'Questo mese',
    reussi: 'Riuscito',
    termine: 'Completato',
    actif: 'Attivo',
    parametres: 'Impostazioni',
    infos_compte: 'Informazioni account',
    adresse_email: 'Indirizzo email',
    email_desc: 'Utilizzato per il tuo abbonamento e notifiche',
    forfait: 'Piano',
    forfait_desc: 'Il tuo abbonamento attuale',
    statut_label: 'Stato',
    statut_desc: 'Stato del tuo abbonamento',
    eco_ce_mois: 'Eco-attività questo mese',
    eco_desc: 'Azzerato il 1° di ogni mese',
    securite: 'Sicurezza',
    token_aria: 'Identificatore Aria (token)',
    token_desc: 'La tua chiave di accesso unica — non condividerla mai',
    chiffrement: 'Crittografia',
    chiffrement_desc: 'I tuoi dati sono crittografati in transito',
    chiffrement_actif: '✓ Attivo',
    donnees_rgpd: 'Dati e privacy',
    exporter_donnees: 'Esporta i miei dati',
    exporter_desc: 'Ricevere una copia dei tuoi dati via email',
    exporter_btn: 'Esporta',
    supprimer_compte: 'Elimina il mio account',
    supprimer_desc: 'Azione irreversibile — elimina tutti i tuoi dati',
    supprimer_btn: 'Elimina',
    support_label: 'Supporto',
    contacter_support: 'Contattare il supporto',
    support_desc: 'Rispondiamo entro 24h',
    ecrire_btn: '✉️ Scrivi',
    mentions_legales: 'Note legali',
    confidentialite: 'Politica sulla privacy',
    voir_btn: 'Visualizza',
    langue_interface: 'Lingua dell\'interfaccia',
    langue_desc: 'Cambia la lingua su tutte le pagine',
    connexion: 'Accedi',
    identifiants: 'Inserisci le tue credenziali Aria FORGEDIS',
    google_btn: 'Continua con Google',
    email_placeholder: 'la-tua@email.com',
    mdp_label: 'Password',
    mdp_oublie: 'Password dimenticata?',
    se_connecter: 'Accedi →',
    pas_de_compte: 'Non hai ancora un account?',
    sinscrire: 'Registrati',
    pas_abonne: 'Non sei ancora abbonato?',
    resilier_titre: 'Annullare l\'abbonamento',
    resilier_texte: 'Il tuo abbonamento Aria Facility sarà annullato alla fine del periodo corrente.',
    supprimer_titre: 'Elimina il mio account',
    supprimer_texte: 'Questa azione è irreversibile. Tutti i tuoi dati verranno eliminati entro 30 giorni.',
    confirmer: 'Conferma annullamento',
    supprimer_confirm: 'Elimina definitivamente',
    annuler: 'Annulla',
    acces_rapide: 'Accesso rapido',
    gerer_abonnement: 'Gestisci abbonamento',
    gerer_sub: 'Cambia, annulla, fatturazione',
    parametres_label: 'Impostazioni',
    parametres_sub: 'Email, token, lingua',
    support_btn: 'Supporto',
    support_sub: 'contact@forgedis.fr',
    essai_gratuit: 'Prova gratuita',
    commencer_essai: 'Inizia la prova gratuita →',
    sans_engagement: 'Senza impegno',
    sans_cb: 'Senza carta di credito',
    resiliable: 'Annulla quando vuoi',
    questions: 'Domande?',
    retour_site: '← Torna al sito',
  },
};

// ═══════════════════════════════════════════════════════════
// MOTEUR I18N
// ═══════════════════════════════════════════════════════════
var _lang = 'fr';
var _rtlLangs = ['sa', 'dz'];

function _load() {
  try { _lang = localStorage.getItem('aria_langue') || 'fr'; } catch(e) {}
  if (!T[_lang]) _lang = 'fr';
}

function _apply() {
  // Direction RTL/LTR
  var rtl = _rtlLangs.indexOf(_lang) !== -1;
  document.documentElement.setAttribute('dir', rtl ? 'rtl' : 'ltr');
  document.documentElement.setAttribute('lang', (_lang === 'sa' || _lang === 'dz') ? 'ar' : _lang);

  // Traduire tous les éléments data-i18n
  document.querySelectorAll('[data-i18n]').forEach(function(el) {
    var key = el.getAttribute('data-i18n');
    var val = _t(key);
    if (val !== key) {
      if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        el.placeholder = val;
      } else {
        el.textContent = val;
      }
    }
  });

  // Traduire les placeholders data-i18n-placeholder
  document.querySelectorAll('[data-i18n-placeholder]').forEach(function(el) {
    var key = el.getAttribute('data-i18n-placeholder');
    el.placeholder = _t(key);
  });

  // Mettre à jour le sélecteur si présent
  var sel = document.getElementById('aria-lang-select');
  if (sel) sel.value = _lang;
}

function _t(key, params) {
  var d = T[_lang] || T.fr;
  var val = d[key] !== undefined ? d[key] : (T.fr[key] || key);
  // Substitution de variables : {prenom}, {count}, {date}...
  if (params && typeof val === 'string') {
    val = val.replace(/\{(\w+)\}/g, function(_, k) {
      return params[k] !== undefined ? params[k] : '{' + k + '}';
    });
  }
  return val;
}

// ═══════════════════════════════════════════════════════════
// SÉLECTEUR DE LANGUE FLOTTANT (premier accès)
// ═══════════════════════════════════════════════════════════
function _injectSelector() {
  // Sélecteur compact dans les paramètres / nav
  // Disponible sur appel : AriaI18n.renderSelect(containerId)
}

function _showFirstTimePicker() {
  var seen = false;
  try { seen = !!localStorage.getItem('aria_langue'); } catch(e) {}
  if (seen) return;

  var overlay = document.createElement('div');
  overlay.id = 'aria-lang-overlay';
  overlay.style.cssText = 'position:fixed;inset:0;background:rgba(7,11,24,0.96);backdrop-filter:blur(12px);z-index:99999;display:flex;align-items:center;justify-content:center;padding:24px;';

  var box = document.createElement('div');
  box.style.cssText = 'background:#0D1426;border:1px solid rgba(255,255,255,0.08);border-radius:20px;padding:40px 32px;max-width:480px;width:100%;text-align:center;';

  var logo = '<div style="font-family:Sora,sans-serif;font-weight:800;font-size:1.4rem;color:#fff;margin-bottom:8px;">FORGE<span style="color:#5BE3D8">DIS</span></div>';
  var title = '<div style="font-family:Sora,sans-serif;font-size:1.5rem;font-weight:800;color:#fff;margin-bottom:8px;">Choose your language</div>';
  var sub = '<div style="font-size:13px;color:#8892A4;margin-bottom:28px;">Choisissez une fois — mémorisé sur toutes les pages</div>';

  var grid = '<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:20px;">';
  LANGUES.forEach(function(l) {
    grid += '<button onclick="AriaI18n.set(\'' + l.code + '\');document.getElementById(\'aria-lang-overlay\').remove();" style="background:#131D35;border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:14px;cursor:pointer;color:#C4CBD8;font-size:14px;font-weight:600;font-family:Inter,sans-serif;transition:all .15s;display:flex;align-items:center;gap:10px;" onmouseover="this.style.borderColor=\'rgba(91,227,216,0.4)\';this.style.color=\'#5BE3D8\';" onmouseout="this.style.borderColor=\'rgba(255,255,255,0.08)\';this.style.color=\'#C4CBD8\';">';
    grid += '<span style="font-size:20px">' + l.flag + '</span><span>' + l.label + '</span>';
    grid += '</button>';
  });
  grid += '</div>';

  var note = '<div style="font-size:12px;color:#6D7799;">Vous pourrez changer la langue à tout moment dans les paramètres</div>';

  box.innerHTML = logo + title + sub + grid + note;
  overlay.appendChild(box);
  document.body.appendChild(overlay);
}

// ═══════════════════════════════════════════════════════════
// RENDU D'UN SELECT INLINE (dans paramètres, nav, etc.)
// ═══════════════════════════════════════════════════════════
function _renderSelect(containerId, style) {
  var container = document.getElementById(containerId);
  if (!container) return;

  var sel = document.createElement('select');
  sel.id = 'aria-lang-select';
  sel.style.cssText = style || 'background:#0D1426;border:1px solid rgba(255,255,255,0.08);border-radius:8px;padding:8px 14px;color:#F0F3FB;font-size:14px;font-family:Inter,sans-serif;cursor:pointer;outline:none;';
  sel.onchange = function() { AriaI18n.set(this.value); };

  LANGUES.forEach(function(l) {
    var opt = document.createElement('option');
    opt.value = l.code;
    opt.textContent = l.flag + ' ' + l.label;
    if (l.code === _lang) opt.selected = true;
    sel.appendChild(opt);
  });

  container.innerHTML = '';
  container.appendChild(sel);
}

// ═══════════════════════════════════════════════════════════
// API PUBLIQUE
// ═══════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════
// EXTENSION 2 — PLURIELS
// Usage : AriaI18n.plural(2, 'exercice', 'exercices')
//         AriaI18n.plural(n, 'enfant', 'enfants', {fr:'enfants',en:'children'})
// ═══════════════════════════════════════════════════════════
function _plural(n, singular, plural_form, overrides) {
  // Règles de pluriel par langue (la plupart sont n>1)
  var needs_plural;
  var lang = _lang;
  // Arabe : pluriel complexe — simplifié à n>1 pour V1
  // Français, Espagnol, Portugais, Allemand, Italien : n > 1
  needs_plural = n > 1 || n === 0;  // en français "0 exercice" → "0 exercice" mais "2 exercices"
  if (lang === 'fr') needs_plural = n > 1;
  if (lang === 'en') needs_plural = n !== 1;
  if (overrides && overrides[lang]) {
    return n + ' ' + overrides[lang];
  }
  return n + ' ' + (needs_plural ? (plural_form || singular + 's') : singular);
}

// ═══════════════════════════════════════════════════════════
// EXTENSION 3 — DATES ET HEURES
// Usage : AriaI18n.date(new Date())
//         AriaI18n.date(new Date(), 'short')   → 07/08/2026
//         AriaI18n.date(new Date(), 'relative') → Aujourd'hui, Hier, Dans 2h
// ═══════════════════════════════════════════════════════════
var _dateLocales = {
  fr: 'fr-FR', en: 'en-US', es: 'es-ES', pt: 'pt-PT',
  de: 'de-DE', it: 'it-IT', ar: 'ar-DZ', dz: 'ar-DZ', sa: 'ar-SA'
};

function _formatDate(d, style) {
  if (!(d instanceof Date) || isNaN(d)) return '';
  var locale = _dateLocales[_lang] || 'fr-FR';
  style = style || 'short';

  if (style === 'relative') {
    var now = new Date();
    var diff = now - d; // ms
    var diffMin  = Math.round(diff / 60000);
    var diffH    = Math.round(diff / 3600000);
    var diffDays = Math.round(diff / 86400000);
    var rel = _t('date_maintenant') || 'À l\'instant';
    if (Math.abs(diffMin) < 1)   return rel;
    if (diffMin > 0 && diffMin < 60) return (_t('date_il_y_a') || 'Il y a') + ' ' + diffMin + ' min';
    if (diffMin < 0 && Math.abs(diffMin) < 60) return (_t('date_dans') || 'Dans') + ' ' + Math.abs(diffMin) + ' min';
    if (diffH > 0 && diffH < 24) return (_t('date_il_y_a') || 'Il y a') + ' ' + diffH + 'h';
    if (diffH < 0 && Math.abs(diffH) < 24) return (_t('date_dans') || 'Dans') + ' ' + Math.abs(diffH) + 'h';
    if (diffDays === 0)  return _t('date_aujourd_hui') || "Aujourd'hui";
    if (diffDays === 1)  return _t('date_hier') || 'Hier';
    if (diffDays === -1) return _t('date_demain') || 'Demain';
    if (diffDays > 0 && diffDays < 7) return (_t('date_il_y_a') || 'Il y a') + ' ' + diffDays + ' j';
    if (diffDays < 0 && Math.abs(diffDays) < 7) return (_t('date_dans') || 'Dans') + ' ' + Math.abs(diffDays) + ' j';
    return d.toLocaleDateString(locale, { day:'2-digit', month:'short' });
  }

  if (style === 'long') {
    return d.toLocaleDateString(locale, { weekday:'long', day:'numeric', month:'long', year:'numeric' });
  }
  if (style === 'time') {
    return d.toLocaleTimeString(locale, { hour:'2-digit', minute:'2-digit' });
  }
  if (style === 'datetime') {
    return d.toLocaleDateString(locale, { day:'2-digit', month:'2-digit', year:'numeric' }) +
           ' ' + d.toLocaleTimeString(locale, { hour:'2-digit', minute:'2-digit' });
  }
  // default = 'short'
  return d.toLocaleDateString(locale, { day:'2-digit', month:'2-digit', year:'numeric' });
}

// ═══════════════════════════════════════════════════════════
// EXTENSION 4 — NOMBRES
// Usage : AriaI18n.number(12500)   → "12 500" (fr) | "12,500" (en)
//         AriaI18n.number(12.5)    → "12,5" (fr) | "12.5" (en)
// ═══════════════════════════════════════════════════════════
function _formatNumber(n, decimals) {
  var locale = _dateLocales[_lang] || 'fr-FR';
  if (decimals !== undefined) {
    return n.toLocaleString(locale, { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
  }
  return n.toLocaleString(locale);
}

// ═══════════════════════════════════════════════════════════
// EXTENSION 5 — DEVISES
// Usage : AriaI18n.currency(12.99)        → "12,99 €" (fr)
//         AriaI18n.currency(12.99, 'USD') → "$12.99" (en)
// ═══════════════════════════════════════════════════════════
var _currencyByLang = {
  fr: 'EUR', en: 'USD', es: 'EUR', pt: 'EUR',
  de: 'EUR', it: 'EUR', ar: 'DZD', dz: 'DZD', sa: 'SAR'
};

function _formatCurrency(amount, currencyCode) {
  var locale = _dateLocales[_lang] || 'fr-FR';
  var currency = currencyCode || _currencyByLang[_lang] || 'EUR';
  try {
    return amount.toLocaleString(locale, { style: 'currency', currency: currency, minimumFractionDigits: 2 });
  } catch(e) {
    return amount.toFixed(2) + ' ' + currency;
  }
}

// ═══════════════════════════════════════════════════════════
// EXTENSION 6 — FUSEAU HORAIRE
// Usage : AriaI18n.localTime(new Date(), timezone)
//         AriaI18n.localTime(new Date(), 'Europe/Paris')
// ═══════════════════════════════════════════════════════════
var _tzByLang = {
  fr: 'Europe/Paris', en: 'America/New_York', es: 'Europe/Madrid',
  pt: 'Europe/Lisbon', de: 'Europe/Berlin', it: 'Europe/Rome',
  ar: 'Africa/Algiers', dz: 'Africa/Algiers', sa: 'Asia/Riyadh'
};

function _localTime(d, timezone) {
  if (!(d instanceof Date) || isNaN(d)) return '';
  var locale = _dateLocales[_lang] || 'fr-FR';
  var tz = timezone || _tzByLang[_lang] || 'Europe/Paris';
  try {
    return d.toLocaleTimeString(locale, { hour:'2-digit', minute:'2-digit', timeZone: tz });
  } catch(e) {
    return d.toLocaleTimeString(locale, { hour:'2-digit', minute:'2-digit' });
  }
}

var AriaI18n = {
  // Lire une clé traduite
  t: function(key, params) { return _t(key, params); },

  // Changer la langue et appliquer partout
  set: function(lang) {
    if (!T[lang]) lang = 'fr';
    _lang = lang;
    try { localStorage.setItem('aria_langue', lang); } catch(e) {}
    _apply();
    // Dispatch event pour les autres scripts qui écoutent
    try {
      w.dispatchEvent(new CustomEvent('aria:langue', { detail: { lang: lang } }));
    } catch(e) {}
  },

  // Langue actuelle
  get: function() { return _lang; },

  // Extension 2 : pluriels
  plural: function(n, singular, plural_form, overrides) {
    return _plural(n, singular, plural_form, overrides);
  },

  // Extension 3 : dates
  date: function(d, style) { return _formatDate(d, style); },

  // Extension 4 : nombres
  number: function(n, decimals) { return _formatNumber(n, decimals); },

  // Extension 5 : devises
  currency: function(amount, currencyCode) { return _formatCurrency(amount, currencyCode); },

  // Extension 6 : heure locale avec fuseau
  localTime: function(d, timezone) { return _localTime(d, timezone); },

  // Rendre un select de langue dans un container
  renderSelect: function(containerId, style) {
    _renderSelect(containerId, style);
  },

  // Liste des langues disponibles
  langues: LANGUES,

  // Appliquer manuellement (utile après injection dynamique de HTML)
  apply: function() { _apply(); },

  // Extension 7 : chargement dynamique d'une langue (architecture future)
  // Usage : AriaI18n.loadLang('ja').then(() => AriaI18n.set('ja'))
  loadLang: function(lang) { return _loadLang(lang); },

  // Chemin des fichiers JSON (configurable avant <script src="aria-i18n.js">)
  // window.AriaI18nJsonPath = '/i18n/';
  jsonPath: '/i18n/'
};

// Exposer globalement
w.AriaI18n = AriaI18n;
w.t = _t; // Raccourci


// ═══════════════════════════════════════════════════════════
// EXTENSION 7 — CHARGEMENT DYNAMIQUE (architecture future)
// Non activé par défaut — conçu pour 20+ langues
// Usage : AriaI18n.loadLang('ja').then(() => AriaI18n.set('ja'))
// Les fichiers JSON doivent être servis depuis /i18n/ja.json
// ═══════════════════════════════════════════════════════════
var _loadedLangs = {};  // Cache des langues chargées dynamiquement

function _loadLang(lang) {
  return new Promise(function(resolve, reject) {
    // Si déjà en mémoire (statique ou chargée), résoudre immédiatement
    if (T[lang] || _loadedLangs[lang]) { resolve(); return; }
    var url = (w.AriaI18n && w.AriaI18n.jsonPath || '/i18n/') + lang + '.json';
    fetch(url)
      .then(function(r) {
        if (!r.ok) throw new Error('Lang not found: ' + lang);
        return r.json();
      })
      .then(function(data) {
        T[lang] = data;
        _loadedLangs[lang] = true;
        resolve();
      })
      .catch(function(e) {
        console.warn('[AriaI18n] Impossible de charger la langue "' + lang + '" :', e.message);
        reject(e);
      });
  });
}

// ═══════════════════════════════════════════════════════════
// INIT AUTOMATIQUE
// ═══════════════════════════════════════════════════════════
function _init() {
  _load();
  _apply();
  _showFirstTimePicker();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', _init);
} else {
  _init();
}

})(window);
