-- Fermeture de 12 tables exposées sans RLS, projet kkznkuwoxoxvapejzytv
-- Préparé le 8 octobre 2026.
-- Constat : aucune de ces tables n'est lue par index.html, et tous les accès observés
-- dans pg_stat_statements viennent des rôles postgres (cron, MCP) et service_role
-- (edge functions), qui ignorent la RLS. Aucun accès anon ni authenticated relevé.
-- Effet : la clé publique anon ne lit et n'écrit plus ces tables. Un utilisateur
-- connecté au dashboard garde l'accès complet par la politique iris_auth_all,
-- comme sur les autres tables du groupe.

begin;

alter table public.email_reconstruction enable row level security;
alter table public.regles_tresorerie   enable row level security;
alter table public.qonto_comptes       enable row level security;
alter table public.inbox_log           enable row level security;
alter table public.destinations        enable row level security;
alter table public.routage_types       enable row level security;
alter table public.routage_cache       enable row level security;
alter table public.referentiels        enable row level security;
alter table public.skills_executions   enable row level security;
alter table public.stg_arristo_lkin    enable row level security;
alter table public._tmp_site           enable row level security;
alter table public._tmp_frag           enable row level security;

create policy iris_auth_all on public.email_reconstruction for all to authenticated using (true) with check (true);
create policy iris_auth_all on public.regles_tresorerie   for all to authenticated using (true) with check (true);
create policy iris_auth_all on public.qonto_comptes       for all to authenticated using (true) with check (true);
create policy iris_auth_all on public.inbox_log           for all to authenticated using (true) with check (true);
create policy iris_auth_all on public.destinations        for all to authenticated using (true) with check (true);
create policy iris_auth_all on public.routage_types       for all to authenticated using (true) with check (true);
create policy iris_auth_all on public.routage_cache       for all to authenticated using (true) with check (true);
create policy iris_auth_all on public.referentiels        for all to authenticated using (true) with check (true);
create policy iris_auth_all on public.skills_executions   for all to authenticated using (true) with check (true);
create policy iris_auth_all on public.stg_arristo_lkin    for all to authenticated using (true) with check (true);
create policy iris_auth_all on public._tmp_site           for all to authenticated using (true) with check (true);
create policy iris_auth_all on public._tmp_frag           for all to authenticated using (true) with check (true);

commit;

-- Retour arrière, table par table si un outil externe utilisant la clé anon casse :
-- alter table public.<table> disable row level security;
