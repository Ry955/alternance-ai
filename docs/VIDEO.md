# Script de la vidéo de démonstration

Durée visée : 4 à 5 minutes. Enregistrement de l'écran avec commentaire audio.
Outil suggéré : l'enregistreur intégré de Windows (`Win + Alt + R`) ou OBS Studio.

Le barème porte sur la créativité de la solution et sur la définition du pipeline. La vidéo
doit donc montrer le pipeline au travail, pas seulement l'application qui fonctionne.

---

## 1. Le problème (30 s)

À l'écran : une offre d'alternance ouverte dans le navigateur.

> « Quand on cherche une alternance, on envoie des dizaines de candidatures. À chaque fois,
> il faut juger si le profil correspond vraiment, puis réécrire une lettre spécifique.
> C'est répétitif et chronophage. Cette application automatise ces deux étapes. »

## 2. L'application en production (1 min)

À l'écran : l'URL publique `https://<nom>.<région>.azurecontainerapps.io`.

- Coller une offre réelle et le profil.
- Cliquer sur **Analyser**.
- Commenter le résultat : le score, les compétences manquantes, la lettre générée.

> « L'application tourne sur Azure Container Apps, en France Central. Le modèle est un
> gpt-4o déployé sur Azure OpenAI en Suède, appelé depuis le conteneur avec une clé
> stockée en secret de l'application. Les deux régions sont dans l'Union européenne :
> le modèle est en Suède parce que c'est la seule région où l'abonnement dispose d'un
> quota, une contrainte que je détaille dans le README. »

Montrer `/health` dans un onglet : il affiche la version déployée, c'est-à-dire le SHA du
commit. Ce détail sert à l'étape 5.

## 3. L'architecture (45 s)

À l'écran : le schéma de la section 2 du README.

> « Le navigateur attaque une Container App exposée en HTTPS, qui appelle Azure OpenAI.
> L'image vient d'un Container Registry privé. J'ai choisi Container Apps plutôt qu'ACI
> parce qu'il gère la mise à l'échelle et le certificat TLS, et plutôt qu'AKS parce qu'un
> cluster Kubernetes serait disproportionné pour un service unique. »

## 4. Le conteneur (45 s)

À l'écran : le `Dockerfile`.

Trois points à souligner, un par phrase :

> « Les dépendances sont installées avant la copie du code : modifier le code ne reconstruit
> que la dernière couche. Le conteneur tourne sous un utilisateur non privilégié, pas sous
> root. Et le `.dockerignore` exclut le `.env` et les clés, pour qu'aucun secret ne se
> retrouve figé dans une couche de l'image. »

## 5. Le pipeline, en direct (1 min 30)

C'est la partie la plus importante. **Faire une vraie modification pendant la vidéo.**

1. Modifier une ligne visible de l'interface, par exemple le titre de la page.
2. `git commit` puis `git push`.
3. Basculer sur l'onglet **Actions** de GitHub et commenter le déroulement :

> « Le pipeline lance d'abord les tests en mode mock, donc sans aucun secret. Il construit
> l'image, démarre le conteneur et interroge `/health` jusqu'à obtenir une réponse : cela
> vérifie que l'image démarre réellement, ce qu'un simple build ne garantit pas. Puis
> Trivy analyse les vulnérabilités. »

4. Enchaîner sur le job de déploiement :

> « Une fois les tests verts, le déploiement s'authentifie sur Azure avec un principal de
> service limité au seul groupe de ressources. L'image est construite directement par le
> registre, puis la Container App est mise à jour en référençant le SHA du commit, jamais
> le tag `latest` : chaque version en ligne est identifiable et un retour arrière consiste
> à redéployer le SHA précédent. »

5. Rafraîchir l'application : la modification est en ligne. Rouvrir `/health` : le numéro
   de version a changé et correspond au nouveau commit.

C'est la démonstration la plus convaincante : du `git push` à la production, sans
intervention manuelle.

## 6. Conclusion (20 s)

> « Le dépôt contient aussi les scripts de création et de suppression de l'infrastructure,
> pour que l'ensemble soit reproductible et que les ressources puissent être supprimées
> afin d'arrêter la facturation. »

---

## Points de vigilance avant d'enregistrer

- Masquer ou ne jamais afficher la page des secrets GitHub, le fichier `.env` et la sortie
  de `az ad sp create-for-rbac`.
- Réveiller l'application avant de lancer l'enregistrement : avec un minimum à zéro replica,
  la première requête subit un démarrage à froid de quelques secondes.
- Vérifier que le pipeline passe au vert **avant** de filmer, pour ne pas enregistrer un échec.
- Fermer les onglets sans rapport et les notifications.
