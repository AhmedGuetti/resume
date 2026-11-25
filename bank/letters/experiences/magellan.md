<!--
Letter paragraphs about bank/experiences/magellan.md (work-study, Oct. 2025 - Sept. 2026).
`by: claude` = an example written by Claude from the bank's bullets. Rewrite it in your
words and set `by: me`. Format and workflow: bank/letters/README.md.
-->

## opener-three-projects
kind: opener
tags: [agents, llm, ownership, autonomy, ai]
by: claude
en: >-
  In one year of work-study at Magellan, I went from joining a 5-person team on an LLM test
  generator to building an agent engine on my own. I would bring that same ownership to the
  {job_title} role at {company}.
fr: >-
  En un an d'alternance chez Magellan, mon rôle a évolué : d'abord dans une équipe de 5 sur
  un générateur de tests par LLM, puis en autonomie complète sur un moteur d'agents.
  J'apporterais cette même autonomie au poste de {job_title} chez {company}.
translated_from: 89d203d0

## opener-spec-bugs
kind: opener
tags: [qa, testing, bugs, specifications, agents, quality]
styles: [story, direct]
by: claude
en: >-
  Some bugs never show up in a code review: they come from a spec that two people read
  differently. At Magellan, that is the kind of bug I built BugPredict to catch.
fr: >-
  Certains bugs n'apparaissent jamais en revue de code : ils viennent d'une spécification
  que deux personnes lisent différemment. Chez Magellan, c'est ce type de bug que BugPredict
  devait détecter.
translated_from: 5713a443

## story-bugpredict
kind: story
tags: [agents, multi-agent, langgraph, qa, testing, jira, confluence, mcp, evaluation, python]
by: claude
en: >-
  At Magellan, I was the main developer of BugPredict, a multi-agent system that predicts
  bugs from specs, Jira tickets and code. It goes after the bugs that come from ambiguous
  specs. Six or so agents read the spec and the code separately, and a last agent checks
  which code implements each requirement. Testers used to paste their context in by hand, so
  I wrote an MCP server and client that fetch it from Jira and Confluence. I also designed
  how we measured it. On BigVul, every bug it flagged was a real one (precision 1.0), and
  three teams use it.
fr: >-
  Chez Magellan, j'ai porté l'essentiel de la conception et du développement de BugPredict,
  un système multi-agents qui prédit les bugs à partir des spécifications, des tickets Jira
  et du code. Il cible les bugs qui naissent de spécifications ambiguës. Une demi-douzaine
  d'agents lisent séparément la spécification et le code, puis un dernier agent vérifie quel
  code implémente chaque exigence. Les testeurs collaient leur contexte à la main : j'ai
  donc écrit un serveur et un client MCP qui vont le chercher dans Jira et Confluence. J'ai
  aussi conçu la façon de l'évaluer. Sur BigVul, chaque bug signalé était réel (précision
  1,0), et trois équipes l'utilisent.
translated_from: 97676ef7

## story-argus
kind: story
tags: [agents, no-code, platform, llm, yaml, react, tools, mcp, automation, workflow]
by: claude
en: >-
  My last project at Magellan was ARGUS, which I built alone. The goal was to let colleagues
  who don't write code, such as testers, create their own agents. They choose the prompt,
  the tools and the MCP connections of each step, in a YAML file or in a web editor I built
  with React Flow. The engine doesn't depend on one LLM vendor: an agent can move from
  Gemini to another provider without being rewritten. New tools plug in through a registry,
  without touching the core. When a team needed something the engine couldn't do yet, I
  built the tool block for it. Other teams trialled ARGUS at pre-production stage.
fr: >-
  Mon dernier projet chez Magellan a été ARGUS, que j'ai construit en autonomie. L'objectif
  : permettre à des collègues qui ne codent pas, comme les testeurs, de créer leurs propres
  agents. Ils choisissent le prompt, les outils et les connexions MCP de chaque étape, dans
  un fichier YAML ou dans un éditeur web que j'ai développé avec React Flow. Le moteur ne
  dépend d'aucun fournisseur de LLM : un agent peut passer de Gemini à un autre fournisseur
  sans être réécrit. Les nouveaux outils se branchent via un registre, sans toucher au cœur
  du moteur. Quand une équipe avait besoin d'une capacité manquante, je développais le bloc
  correspondant. D'autres équipes ont testé ARGUS en préproduction.
translated_from: 8b2238c1

## story-atas
kind: story
tags: [agents, tool-calling, human-in-the-loop, mcp, teamwork, ui, python, testing, llm]
by: claude
en: >-
  I started at Magellan on aTaS, a 5-person team building an LLM test-case generator. My
  part was to turn a single static LLM call into a real agent, with tool calling and MCP
  connections. I then built the human-in-the-loop step: when the agent is missing
  information, it pauses and asks the tester. The hard part was keeping the final results
  reliable after those interruptions. I also rebuilt the interface: a tester loads a user
  story, answers the agent's questions, and gets a report in a standard template to edit and
  save. The generator later became the first agent of the testing portal that hosts
  BugPredict.
fr: >-
  J'ai commencé chez Magellan sur aTaS, au sein d'une équipe de 5 qui développait un
  générateur de cas de test par LLM. Ma part : transformer un simple appel LLM statique en
  véritable agent, avec appel d'outils et connexions MCP. J'ai ensuite construit l'étape
  d'humain dans la boucle : quand une information manque à l'agent, il s'arrête et interroge
  le testeur. La difficulté était de garder des résultats fiables malgré ces interruptions.
  J'ai aussi refait l'interface : le testeur charge une user story, répond aux questions de
  l'agent et obtient un rapport dans un modèle standard, qu'il peut modifier et enregistrer.
  Le générateur est ensuite devenu le premier agent du portail de test qui héberge
  BugPredict.
translated_from: d90aab2b

## story-evaluation
kind: story
tags: [evaluation, benchmark, research, llm-as-judge, metrics, agents, ml]
by: claude
en: >-
  BugPredict taught me that an agent is only as credible as its evaluation. I designed the
  protocol: Defects4J and BigVul as ground truth, clean twin files as negative controls, and
  an LLM judge to match each prediction to a known bug. The result was honest rather than
  flattering: precision 1.0 on BigVul, but recall 0.235. Later I benchmarked an ARGUS agent
  that checks specs against code. It had no false positives but missed about 60% of bugs,
  because those datasets target code-level bugs rather than misread specs. Knowing what a
  system misses is what lets a team trust what it finds.
fr: >-
  BugPredict m'a appris qu'un agent n'est crédible que si son évaluation l'est. J'ai conçu
  le protocole : Defects4J et BigVul comme vérité terrain, des fichiers « jumeaux » sans bug
  comme contrôles négatifs, et un LLM juge pour rapprocher chaque prédiction d'un bug connu.
  Le résultat était honnête plutôt que flatteur : précision de 1,0 sur BigVul, mais rappel
  de 0,235. J'ai ensuite évalué un agent ARGUS qui confronte spécifications et code. Aucun
  faux positif, mais environ 60 % des bugs manqués, car ces jeux de données visent des bugs
  de code plutôt que des spécifications mal comprises. Savoir ce qu'un système manque, c'est
  ce qui permet à une équipe de faire confiance à ce qu'il trouve.
translated_from: e519a1bd

## story-production
kind: story
tags: [production, ci-cd, gitlab, devops, deployment, reliability, documentation]
by: claude
en: >-
  The day BugPredict was first connected to aTaS, it failed in production. I spent the full
  day tracking it down to a configuration error caused by gaps in aTaS's support. After
  that, I set up the GitLab CI/CD pipeline that builds, versions and releases the tool on
  every merge to prod. I kept it running on a self-hosted Windows runner, despite the
  restrictions of corporate laptops. When the project ended, I handed it over with
  configuration docs on Confluence and a narrated demo video, so the team could run it
  without me.
fr: >-
  Le jour où BugPredict a été connecté pour la première fois à aTaS, il a planté en
  production. J'ai passé la journée entière à remonter jusqu'à une erreur de configuration,
  due à des lacunes dans le support d'aTaS. J'ai ensuite mis en place le pipeline CI/CD
  GitLab qui construit, versionne et publie l'outil à chaque fusion vers la prod. Je l'ai
  fait tourner sur un runner Windows auto-hébergé, malgré les restrictions des postes de
  l'entreprise. À la fin du projet, je l'ai transmis avec une documentation de configuration
  sur Confluence et une vidéo de démonstration commentée, pour que l'équipe puisse s'en
  servir sans moi.
translated_from: 37c601c6

## story-qa-ai
kind: story
tags: [qa, testing, cucumber, xray, jira, confluence, agile, agents, llm, api-testing, ownership]
by: claude
en: >-
  At Magellan I was an AI engineer inside a QA team, not next to it. Day to day, I worked
  the way the testers did: tasks in Jira, Cucumber scenarios managed in Jira Xray, test
  reports and documentation on Confluence, and API testing for RATP. That is what shaped the
  agents I built. aTaS generates test cases in the format the team already used, BugPredict
  pulls its context straight from Jira and Confluence, and ARGUS lets testers assemble their
  own agents without code. As the owner of those projects, I reviewed and approved every
  merge request before it reached production. At the end of the work-study, I was offered a
  position to stay.
fr: >-
  Chez Magellan, j'étais un ingénieur IA au sein d'une équipe QA, et non à côté d'elle. Au
  quotidien, je travaillais comme les testeurs : tâches dans Jira, scénarios Cucumber gérés
  dans Jira Xray, rapports de test et documentation sur Confluence, et tests des API de la
  RATP. C'est ce qui a façonné les agents que j'ai construits. aTaS génère des cas de test
  dans le format que l'équipe utilisait déjà, BugPredict va chercher son contexte
  directement dans Jira et Confluence, et ARGUS permet aux testeurs d'assembler leurs
  propres agents sans coder. Responsable de ces projets, je relisais et validais chaque
  merge request avant son passage en production. À la fin de l'alternance, on m'a proposé de
  rester.
translated_from: b85926d8
