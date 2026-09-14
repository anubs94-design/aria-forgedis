-- Sécuriser get_portal_context : retirer EXECUTE de PUBLIC/anon
-- Accorder uniquement à authenticated et service_role
REVOKE EXECUTE ON FUNCTION public.get_portal_context() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.get_portal_context() FROM anon;
GRANT EXECUTE ON FUNCTION public.get_portal_context() TO authenticated;
GRANT EXECUTE ON FUNCTION public.get_portal_context() TO service_role;

-- Vérification
SELECT grantee, privilege_type
FROM information_schema.role_routine_grants
WHERE routine_name = 'get_portal_context'
  AND routine_schema = 'public'
ORDER BY grantee;
