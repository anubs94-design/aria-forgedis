// ─────────────────────────────────────────────────────────────────────────────
// MODULE CLIENTS ENTREPRISE — Aria Industrial
// Partagé entre : service-client, comptabilité, logistique, dirigeant, achats
// ─────────────────────────────────────────────────────────────────────────────

var _clientsDB = [];
var _clientSelectionne = null;

var TACHES_PAR_POSTE = {
  service_client: [
    { label: "📞 Rappeler le client",    titre: "Rappel téléphonique",    priorite: 2 },
    { label: "📧 Envoyer un devis",      titre: "Envoi devis",            priorite: 2 },
    { label: "🎫 Ouvrir ticket SAV",     titre: "Ticket SAV",             priorite: 1 },
    { label: "🔄 Relance impayé",        titre: "Relance impayé",         priorite: 1 },
    { label: "📋 CR visite",             titre: "CR visite client",        priorite: 3 },
  ],
  comptabilite: [
    { label: "🧾 Émettre une facture",   titre: "Facturation client",     priorite: 2 },
    { label: "📬 Relance paiement",      titre: "Relance paiement",       priorite: 1 },
    { label: "💳 Vérifier impayés",      titre: "Vérif. impayés",         priorite: 1 },
    { label: "📊 Bilan client",          titre: "Bilan financier client", priorite: 3 },
  ],
  logistique: [
    { label: "📦 Préparer livraison",    titre: "Préparation livraison",  priorite: 2 },
    { label: "🚚 Planifier livraison",   titre: "Planif. livraison",      priorite: 2 },
    { label: "📬 Confirmer réception",   titre: "Confirmation réception", priorite: 3 },
    { label: "🔁 Gérer un retour",       titre: "Gestion retour",         priorite: 1 },
  ],
  achats: [
    { label: "📝 Bon de commande",       titre: "Bon de commande client", priorite: 2 },
    { label: "🤝 Négo tarifaire",        titre: "Négociation tarifaire",  priorite: 3 },
    { label: "📋 MàJ contrat",           titre: "MàJ contrat client",     priorite: 3 },
  ],
  dirigeant: [
    { label: "🤝 RDV stratégique",       titre: "Réunion stratégique",    priorite: 3 },
    { label: "📈 Revue de compte",        titre: "Revue compte client",    priorite: 3 },
    { label: "⚠️ Gestion litige",        titre: "Gestion litige",          priorite: 1 },
  ],
  technicien_sav: [
    { label: "🔧 Intervention",          titre: "Intervention technique",  priorite: 2 },
    { label: "📋 Rapport intervention",  titre: "Rapport intervention",    priorite: 3 },
    { label: "🔄 SAV garantie",          titre: "SAV sous garantie",       priorite: 1 },
  ],
};

async function chargerClients() {
  var el = document.getElementById('clients-liste');
  if (el) el.innerHTML = '<div style="color:var(--muted);font-size:13px">Chargement...</div>';
  var r = await api('/industrial/clients-entreprise', { token: getToken(), entreprise_id: getEntrepriseId() }, 'GET');
  _clientsDB = r.clients || [];
  afficherListeClients(_clientsDB);
}

function afficherListeClients(liste) {
  var el = document.getElementById('clients-liste');
  if (!el) return;
  if (!liste.length) {
    el.innerHTML = '<div class="empty-state"><div class="es-ic">👥</div>Aucun client. Ajoutez votre premier client.</div>';
    return;
  }
  el.innerHTML = liste.map(function(c) {
    var badge = c.statut === 'actif' ? 'ok' : c.statut === 'prospect' ? 'warn' : '';
    var badgeLabel = c.statut === 'actif' ? 'Actif' : c.statut === 'prospect' ? 'Prospect' : 'Inactif';
    return '<div class="row-item" onclick="ouvrirFicheClient(\'' + c.id + '\')" style="cursor:pointer">' +
      '<div class="ri-main">' +
      '<div class="ri-title">' + esc(c.nom) + ' <span class="badge badge-' + badge + '">' + badgeLabel + '</span></div>' +
      '<div class="ri-sub">' + (c.contact ? esc(c.contact) + ' — ' : '') + esc(c.telephone || '') + (c.secteur ? ' | ' + esc(c.secteur) : '') + '</div>' +
      '</div>' +
      '<div class="ri-actions">' +
      '<button class="btn-act btn-amber btn-sm" onclick="event.stopPropagation();ouvrirFicheClient(\'' + c.id + '\')">Fiche</button>' +
      '<button class="btn-act btn-err btn-sm" onclick="event.stopPropagation();supprimerClientUI(\'' + c.id + '\',\'' + esc(c.nom) + '\')">✕</button>' +
      '</div></div>';
  }).join('');
}

function rechercherClients(q) {
  if (!q.trim()) { afficherListeClients(_clientsDB); return; }
  var ql = q.toLowerCase();
  afficherListeClients(_clientsDB.filter(function(c) {
    return (c.nom||'').toLowerCase().includes(ql) ||
           (c.contact||'').toLowerCase().includes(ql) ||
           (c.email||'').toLowerCase().includes(ql) ||
           (c.secteur||'').toLowerCase().includes(ql);
  }));
}

async function ouvrirFicheClient(clientId) {
  _clientSelectionne = _clientsDB.find(function(c){ return c.id === clientId; });
  if (!_clientSelectionne) return;
  var c = _clientSelectionne;
  var poste = typeof POSTE_COURANT !== 'undefined' ? POSTE_COURANT : 'service_client';
  var taches_poste = TACHES_PAR_POSTE[poste] || [];
  var rt = await api('/industrial/taches-client', { token: getToken(), client_id: clientId }, 'GET');
  var taches_actives = (rt.taches || []).filter(function(t){ return t.statut !== 'termine'; });
  var ficheEl = document.getElementById('client-fiche-contenu');
  if (!ficheEl) return;
  ficheEl.innerHTML =
    '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px">' +
    '<div><h2 style="margin:0">' + esc(c.nom) + '</h2>' +
    '<span class="badge badge-' + (c.statut==='actif'?'ok':c.statut==='prospect'?'warn':'') + '">' + esc(c.statut) + '</span>' +
    (c.secteur ? '<span style="color:var(--muted);font-size:12px;margin-left:8px">' + esc(c.secteur) + '</span>' : '') +
    '</div><button class="btn-act btn-ghost btn-sm" onclick="editerClientUI()">✏️ Modifier</button></div>' +
    '<div class="form-grid" style="margin-bottom:16px">' +
    (c.contact   ? '<div class="form-group"><label>Contact</label><div class="input-field" style="background:var(--card)">' + esc(c.contact) + '</div></div>' : '') +
    (c.email     ? '<div class="form-group"><label>Email</label><a href="mailto:' + esc(c.email) + '" class="input-field" style="background:var(--card);display:block">' + esc(c.email) + '</a></div>' : '') +
    (c.telephone ? '<div class="form-group"><label>Téléphone</label><a href="tel:' + esc(c.telephone) + '" class="input-field" style="background:var(--card);display:block">' + esc(c.telephone) + '</a></div>' : '') +
    (c.adresse   ? '<div class="form-group" style="grid-column:1/-1"><label>Adresse</label><div class="input-field" style="background:var(--card)">' + esc(c.adresse) + '</div></div>' : '') +
    (c.notes     ? '<div class="form-group" style="grid-column:1/-1"><label>Notes</label><div class="input-field" style="background:var(--card);white-space:pre-line">' + esc(c.notes) + '</div></div>' : '') +
    '</div>' +
    '<div class="section-head"><h2>Créer une tâche pour ce client</h2></div>' +
    '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px">' +
    taches_poste.map(function(t) {
      return '<button class="btn-act btn-amber btn-sm" onclick="creerTacheClientRapide(\'' + clientId + '\',\'' + esc(c.nom).replace(/'/g,"\\'") + '\',\'' + esc(t.titre).replace(/'/g,"\\'") + '\',' + t.priorite + ',\'' + poste + '\')">' + t.label + '</button>';
    }).join('') +
    '<button class="btn-act btn-ghost btn-sm" onclick="creerTacheClientPerso(\'' + clientId + '\',\'' + esc(c.nom).replace(/'/g,"\\'") + '\')">✏️ Personnalisée</button>' +
    '</div>' +
    '<div class="section-head"><h2>Tâches en cours (' + taches_actives.length + ')</h2></div>' +
    (taches_actives.length ? taches_actives.map(function(t) {
      var col = t.priorite===1?'#E24B4A':t.priorite===2?'#F4A259':'var(--muted)';
      return '<div class="row-item"><div class="ri-main"><div class="ri-title" style="color:'+col+'">' + esc(t.titre) + '</div>' +
        '<div class="ri-sub">' + esc(t.statut) + (t.poste_demandeur?' — '+esc(t.poste_demandeur):'') + (t.echeance?' — ⏰ '+fmtDate(t.echeance):'') + '</div></div></div>';
    }).join('') : '<div class="empty-state" style="padding:12px 0">Aucune tâche active.</div>');
  document.getElementById('clients-liste-panel').style.display = 'none';
  document.getElementById('client-fiche-panel').style.display = 'block';
}

function fermerFicheClient() {
  document.getElementById('clients-liste-panel').style.display = 'block';
  document.getElementById('client-fiche-panel').style.display = 'none';
  _clientSelectionne = null;
}

async function creerTacheClientRapide(clientId, clientNom, titre, priorite, poste) {
  var r = await api('/industrial/client/creer-tache', {
    token: getToken(), entreprise_id: getEntrepriseId(),
    client_id: clientId, client_nom: clientNom,
    titre: titre, priorite: priorite, poste_demandeur: poste,
  });
  if (r.ok) { if (typeof notif==='function') notif('✅ Tâche créée : ' + r.tache.titre); ouvrirFicheClient(clientId); }
  else { if (typeof notif==='function') notif('❌ ' + (r.erreur||'Erreur'), true); }
}

async function creerTacheClientPerso(clientId, clientNom) {
  var poste = typeof POSTE_COURANT !== 'undefined' ? POSTE_COURANT : 'service_client';
  var titre = await ariaPrompt('Titre de la tâche pour ' + clientNom + ' :');
  if (!titre) return;
  var r = await api('/industrial/client/creer-tache', {
    token: getToken(), entreprise_id: getEntrepriseId(),
    client_id: clientId, client_nom: clientNom,
    titre: titre, priorite: 2, poste_demandeur: poste,
  });
  if (r.ok) { if (typeof notif==='function') notif('✅ Tâche créée'); ouvrirFicheClient(clientId); }
}

async function supprimerClientUI(clientId, nom) {
  var ok = await ariaConfirm('Supprimer le client "' + nom + '" ?', 'Supprimer client', true);
  if (!ok) return;
  var r = await api('/industrial/client/supprimer', { token: getToken(), client_id: clientId });
  if (r.ok) chargerClients();
}

function afficherFormulaireClient(clientExistant) {
  var c = clientExistant || {};
  var el = document.getElementById('client-form-contenu');
  if (!el) return;
  el.innerHTML =
    '<div class="form-grid">' +
    '<div class="form-group" style="grid-column:1/-1"><label>Nom client *</label>' +
    '<input type="text" id="cf-nom" class="input-field" value="' + esc(c.nom||'') + '" placeholder="Nom de l\'entreprise cliente"></div>' +
    '<div class="form-group"><label>Contact</label><input type="text" id="cf-contact" class="input-field" value="' + esc(c.contact||'') + '" placeholder="Prénom Nom"></div>' +
    '<div class="form-group"><label>Email</label><input type="email" id="cf-email" class="input-field" value="' + esc(c.email||'') + '"></div>' +
    '<div class="form-group"><label>Téléphone</label><input type="tel" id="cf-tel" class="input-field" value="' + esc(c.telephone||'') + '"></div>' +
    '<div class="form-group"><label>Secteur</label><input type="text" id="cf-secteur" class="input-field" value="' + esc(c.secteur||'') + '" placeholder="BTP, Commerce, Santé..."></div>' +
    '<div class="form-group"><label>Statut</label><select id="cf-statut" class="input-field">' +
    '<option value="actif"' + (c.statut==='actif'?' selected':'') + '>Actif</option>' +
    '<option value="prospect"' + (c.statut==='prospect'?' selected':'') + '>Prospect</option>' +
    '<option value="inactif"' + (c.statut==='inactif'?' selected':'') + '>Inactif</option></select></div>' +
    '<div class="form-group" style="grid-column:1/-1"><label>Adresse</label><input type="text" id="cf-adresse" class="input-field" value="' + esc(c.adresse||'') + '"></div>' +
    '<div class="form-group" style="grid-column:1/-1"><label>Notes</label><textarea id="cf-notes" class="input-field" rows="3">' + esc(c.notes||'') + '</textarea></div>' +
    '</div>';
  document.getElementById('clients-liste-panel').style.display = 'none';
  document.getElementById('client-fiche-panel').style.display = 'none';
  document.getElementById('client-form-panel').style.display = 'block';
}

function editerClientUI() { if (_clientSelectionne) afficherFormulaireClient(_clientSelectionne); }

async function sauvegarderClient() {
  var nom = document.getElementById('cf-nom').value.trim();
  if (!nom) { if (typeof notif==='function') notif('❌ Le nom est requis', true); return; }
  var data = {
    token: getToken(), entreprise_id: getEntrepriseId(), nom: nom,
    contact:   document.getElementById('cf-contact').value,
    email:     document.getElementById('cf-email').value,
    telephone: document.getElementById('cf-tel').value,
    secteur:   document.getElementById('cf-secteur').value,
    statut:    document.getElementById('cf-statut').value,
    adresse:   document.getElementById('cf-adresse').value,
    notes:     document.getElementById('cf-notes').value,
  };
  var r;
  if (_clientSelectionne) { data.client_id = _clientSelectionne.id; r = await api('/industrial/client/modifier', data); }
  else { r = await api('/industrial/client/creer', data); }
  if (r.ok || r.client) {
    if (typeof notif==='function') notif('✅ Client ' + (_clientSelectionne ? 'modifié' : 'créé'));
    annulerFormClient(); chargerClients();
  } else { if (typeof notif==='function') notif('❌ ' + (r.erreur||'Erreur'), true); }
}

function annulerFormClient() {
  _clientSelectionne = null;
  document.getElementById('client-form-panel').style.display = 'none';
  document.getElementById('clients-liste-panel').style.display = 'block';
}
