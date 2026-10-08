/**
 * Générateur du jeu de démonstration : un SoC fictif complet, 9 182 exigences,
 * 9 niveaux (ERS, SDS, DDS, ANS, FWS, VP, ANV, FWT, VAL), 11 sous-systèmes, 45 blocs.
 *
 * EXPORTS
 *   seedDocs()  → { "NIVEAU|CODE_SOUS_SYSTÈME": JSON Tiptap }  (99 documents, certains vides)
 *   SESSIONS    → deux jeux de résultats fictifs { n1003, n1004 } : { label, ids, results: {métrique → résultat} }
 *   SUB_LIST    → [{ code, nom }] des sous-systèmes, dans l'ordre d'affichage
 *   TOTAL       → nombre d'exigences générées
 *
 * DÉROULÉ (dans l'ordre du fichier)
 *   1. blocs       : 45 blocs fonctionnels (F_OLD rédigés en objets, F_NEW en écriture compacte B(...)).
 *                    Chaque bloc porte son vocabulaire : registres, signaux, fonctions du driver,
 *                    événements, exigences client rédigées à la main (`ers`) et, pour l'analogique,
 *                    ses performances paramétriques (`par`).
 *   2. gabarits T  : phrases types par niveau, remplies avec le vocabulaire du bloc (ctx).
 *   3. graphe      : crée les nœuds niveau par niveau (ERS → SDS → DDS/ANS/FWS → plans) avec leurs liens.
 *   4. plans       : énoncés et métriques des items de vérification.
 *   5. numérotation: IDs « NIVEAU-SOUS-SYSTÈME-NNN » attribués dans l'ordre des documents.
 *   6. JSON Tiptap : un document par (niveau, sous-système), titres par bloc et par branche.
 *   7. résultats   : deux sessions, la n1003 plus dégradée que la n1004 (pour comparer).
 *
 * DÉTERMINISME — IMPORTANT
 *   Tout tire du générateur pseudo-aléatoire R (graine fixe). Le même fichier produit toujours
 *   exactement les mêmes exigences, IDs et résultats. Corollaire : AJOUTER, RETIRER OU RÉORDONNER
 *   UN SEUL APPEL À R() décale tout ce qui suit (IDs, énoncés, statuts). Si vous modifiez ce fichier :
 *     - les IDs cités en dur dans outils/generer_maquettes.py (ERS-IO-020, SDS-IO-002…) peuvent ne plus
 *       désigner les mêmes exigences : régénérez les maquettes et relisez-les ;
 *     - les documents modifiés et sauvegardés dans le navigateur ne correspondent plus : incrémentez
 *       KEY dans app.js.
 *   Les résultats utilisent un hachage du nom de métrique (hash) pour rester stables, mais result()
 *   appelle encore int()/pick() pour certaines valeurs : même remarque.
 *
 * TROUS VOLONTAIRES (pour que la démo montre des anomalies)
 *   ~1 exigence client racine sur 37 sans aucune dérivée (non tracée), quelques SDS sans DDS,
 *   quelques items de plan sans métrique, plans requis non couverts, résultats absents,
 *   à rejouer (stale) ou en attente de double validation (pending).
 */
// mulberry32 : PRNG 32 bits simple et reproductible.
function rng(seed) { return () => { seed |= 0; seed = (seed + 0x6D2B79F5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296 } }
const R = rng(20261007)
const pick = a => a[Math.floor(R() * a.length)]
const int = (a, b) => a + Math.floor(R() * (b - a + 1))
// FNV-1a ramené dans [0, 1) : sert à tirer les résultats à partir du nom de métrique.
const hash = s => { let h = 2166136261; for (const c of s) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619) } return ((h >>> 0) % 100000) / 100000 }
const fr = n => String(n).replace('.', ',')

/* ---------- blocs ----------
 * Champs d'un bloc :
 *   k    code court (aussi utilisé dans les noms de métriques, en minuscules)
 *   nom  titre de section dans les documents ; de : complément « du/de la/des … » pour les phrases
 *   blk  nom du module RTL ; t : 'num' ou 'ana' (un bloc 'ana' a une branche ANS/ANV et des `par`)
 *   inst nombre d'instances (génère des exigences SDS « instance par instance »)
 *   regs [[REGISTRE, CHAMP]], sig : signaux, api : fonctions du driver, ev : événements
 *   ers  exigences client racines, rédigées à la main — c'est ce qui rend le jeu lisible
 *   der  [[index de l'ERS parente, texte]] exigences client dérivées rédigées à la main
 *   par  performances analogiques [code, grandeur, condition, contexte, suffixe de métrique, critère]
 */
const F_OLD = [
  { k: 'DMA', de: 'du contrôleur DMA', nom: 'Contrôleur DMA', blk: 'dma_top', t: 'num', regs: [['CTRL', 'EN'], ['SRC', 'ADDR'], ['DST', 'ADDR'], ['LEN', 'COUNT'], ['STATUS', 'BUSY'], ['STATUS', 'ERRCODE'], ['PRIO', 'LEVEL'], ['LLI', 'NEXT']], sig: ['irq_done', 'irq_err', 'dma_req', 'dma_ack'], api: ['dma_start', 'dma_abort', 'dma_wait', 'dma_link'],
    ev: ['la fin d’un transfert', 'une réponse SLVERR du bus', 'une demande d’abandon logiciel', 'le chargement du descripteur suivant', 'une requête périphérique'],
    ers: ['Le contrôleur DMA doit offrir 8 canaux de transfert indépendants.', 'Un transfert en cours doit pouvoir être interrompu par logiciel sans corrompre la mémoire de destination.', 'Toute erreur de bus doit être signalée au processeur en moins de 16 cycles d’horloge.', 'Les transferts mémoire vers périphérique doivent supporter un handshake matériel.', 'Chaque canal doit pouvoir être programmé avec une priorité parmi quatre niveaux.', 'Le contrôleur doit enchaîner des transferts décrits en liste chaînée sans intervention du processeur.'],
    der: [[2, 'Le logiciel doit pouvoir distinguer une erreur esclave d’une erreur de décodage d’adresse.'], [4, 'Deux canaux de même priorité doivent être servis à tour de rôle.']] },
  { k: 'UART', de: 'de l’UART', nom: 'UART', blk: 'uart_core', t: 'num', regs: [['BAUD', 'DIV'], ['LCR', 'PARITY'], ['LCR', 'STOP'], ['FIFO', 'LEVEL'], ['ISR', 'OVR'], ['ISR', 'FERR'], ['MCR', 'RTSEN']], sig: ['uart_tx', 'uart_rx', 'irq_uart', 'uart_rts_n'], api: ['uart_init', 'uart_write', 'uart_read', 'uart_set_baud'],
    ev: ['la réception d’un octet', 'une erreur de parité', 'le remplissage de la FIFO au-delà du seuil', 'la détection d’une ligne inactive', 'un débordement de la FIFO de réception'],
    ers: ['L’UART doit supporter les débits de 9 600 à 3 000 000 bauds avec une erreur inférieure à 2 %.', 'L’UART doit disposer de FIFO d’émission et de réception d’au moins 32 octets.', 'Les erreurs de parité, de trame et de débordement doivent être détectées et signalées.', 'L’UART doit supporter le contrôle de flux matériel RTS et CTS.', 'L’UART doit accepter des trames de 7 ou 8 bits de données avec 1 ou 2 bits de stop.', 'La détection d’une ligne inactive doit permettre de délimiter les trames reçues.'],
    der: [[1, 'Un seuil de remplissage programmable de la FIFO de réception doit déclencher une interruption.']] },
  { k: 'SPI', de: 'du maître SPI', nom: 'Maître SPI', blk: 'spi_master', t: 'num', regs: [['CFG', 'CPOL'], ['CFG', 'CPHA'], ['CFG', 'WIDTH'], ['DATA', 'TX'], ['SR', 'BUSY'], ['CS', 'SEL'], ['CLKDIV', 'RATIO']], sig: ['spi_sclk', 'spi_mosi', 'spi_miso', 'spi_cs_n'], api: ['spi_config', 'spi_xfer', 'spi_xfer_dma'],
    ev: ['la fin d’un mot transmis', 'la désélection de l’esclave', 'une écriture dans DATA pendant un transfert', 'la fin d’une rafale DMA'],
    ers: ['Le maître SPI doit supporter les quatre modes de polarité et de phase d’horloge.', 'Le maître SPI doit piloter jusqu’à 4 esclaves par des sélections de puce distinctes.', 'La fréquence SPI doit être programmable jusqu’à 50 MHz.', 'Le maître SPI doit transférer des mots de 4 à 32 bits.', 'Le maître SPI doit pouvoir enchaîner des transferts par DMA sans intervention logicielle.'],
    der: [[2, 'La fréquence doit pouvoir être modifiée entre deux transferts sans réinitialiser le bloc.']] },
  { k: 'I2C', de: 'du contrôleur I2C', nom: 'Contrôleur I2C', blk: 'i2c_ctrl', t: 'num', regs: [['CR', 'MODE'], ['ADDR', 'A10'], ['SR', 'ARBLOST'], ['SR', 'NACK'], ['TIMING', 'SCLL'], ['RECOVER', 'PULSES']], sig: ['i2c_scl', 'i2c_sda', 'irq_i2c'], api: ['i2c_init', 'i2c_master_xfer', 'i2c_bus_recover'],
    ev: ['une perte d’arbitrage', 'un NACK de l’esclave', 'un étirement d’horloge par l’esclave', 'la détection d’un bus bloqué'],
    ers: ['Le contrôleur I2C doit supporter les modes standard, rapide et rapide plus jusqu’à 1 MHz.', 'Le contrôleur I2C doit gérer l’adressage sur 7 et sur 10 bits.', 'Une perte d’arbitrage en configuration multi-maître doit être détectée et signalée.', 'Le contrôleur doit respecter l’étirement d’horloge imposé par un esclave.', 'Un bus bloqué doit pouvoir être libéré par logiciel en générant 9 impulsions d’horloge.'],
    der: [] },
  { k: 'TMR', de: 'des timers', nom: 'Timers', blk: 'tmr_bank', t: 'num', regs: [['LOAD', 'VAL'], ['VALUE', 'CNT'], ['CTRL', 'AUTORELOAD'], ['PRESC', 'DIV'], ['PWM', 'DUTY'], ['CAPT', 'STAMP'], ['CTRL', 'DBGSTOP']], sig: ['irq_tmr', 'pwm_out', 'tmr_capt_in'], api: ['tmr_start', 'tmr_set_period', 'tmr_set_duty', 'tmr_capture'],
    ev: ['l’expiration du compteur', 'un front sur l’entrée de capture', 'l’arrêt du processeur en debug', 'le rechargement automatique'],
    ers: ['Le sous-système doit offrir 4 timers 32 bits à rechargement automatique.', 'Chaque timer doit pouvoir générer un signal PWM de rapport cyclique programmable.', 'L’expiration d’un timer doit pouvoir réveiller le système depuis le mode veille.', 'Chaque timer doit offrir un mode capture sur front externe.', 'Le prédiviseur de chaque timer doit être programmable de 1 à 65 536.', 'Les timers doivent pouvoir s’arrêter quand le processeur est stoppé par le débogueur.'],
    der: [[3, 'Le mode capture doit horodater l’événement à un cycle d’horloge près.']] },
  { k: 'IRQ', de: 'du contrôleur d’interruptions', nom: 'Contrôleur d’interruptions', blk: 'irq_ctrl', t: 'num', regs: [['ENABLE', 'MASK'], ['PENDING', 'SRC'], ['PRIO', 'LEVEL'], ['ACK', 'ID'], ['SWTRIG', 'SRC']], sig: ['irq_out', 'nmi', 'irq_ack'], api: ['irq_enable', 'irq_set_prio', 'irq_ack', 'irq_trigger'],
    ev: ['l’arrivée d’une source de priorité supérieure', 'l’acquittement de la source servie', 'un déclenchement logiciel', 'une erreur critique'],
    ers: ['Le contrôleur d’interruptions doit gérer 64 sources avec 8 niveaux de priorité.', 'Une interruption non masquable doit être disponible pour les erreurs critiques.', 'La latence entre l’événement et la requête au processeur doit être inférieure à 10 cycles.', 'Chaque source doit pouvoir être masquée individuellement.', 'Chaque source doit pouvoir être déclenchée par logiciel pour les tests.'],
    der: [[0, 'Deux sources de même priorité doivent être servies dans l’ordre de leur numéro.']] },
  { k: 'GPIO', de: 'des entrées-sorties', nom: 'Entrées-sorties générales', blk: 'gpio_bank', t: 'num', regs: [['DIR', 'OUT'], ['DATA', 'VAL'], ['IRQCFG', 'EDGE'], ['PULL', 'CFG'], ['DEBOUNCE', 'MS'], ['BSR', 'SET']], sig: ['gpio_pad', 'irq_gpio'], api: ['gpio_config', 'gpio_write_mask', 'gpio_on_edge'],
    ev: ['un front sur une broche configurée en interruption', 'l’écriture d’un masque de broches', 'la fin du délai d’anti-rebond', 'l’entrée en veille'],
    ers: ['Le bloc GPIO doit offrir 32 broches configurables individuellement en entrée ou en sortie.', 'Chaque broche doit pouvoir déclencher une interruption sur front montant, descendant ou sur niveau.', 'Les résistances de tirage doivent être programmables broche par broche.', 'Un anti-rebond programmable de 1 à 255 ms doit être disponible sur chaque entrée.', 'Le logiciel doit pouvoir modifier un sous-ensemble de broches de façon atomique.', 'L’état des sorties doit être conservé pendant la veille.'],
    der: [[3, 'L’anti-rebond doit pouvoir être désactivé broche par broche.']] },
  { k: 'WDT', de: 'du chien de garde', nom: 'Chien de garde', blk: 'wdt_core', t: 'num', regs: [['CTRL', 'EN'], ['WINDOW', 'MIN'], ['TIMEOUT', 'MAX'], ['KICK', 'KEY'], ['RSTCAUSE', 'SRC']], sig: ['wdt_rst', 'irq_wdt_early'], api: ['wdt_start', 'wdt_kick', 'wdt_reset_cause'],
    ev: ['un rafraîchissement hors fenêtre', 'l’expiration du délai', 'une tentative de désactivation', 'le redémarrage après un reset'],
    ers: ['Le sous-système doit offrir un chien de garde fenêtré.', 'Le délai du chien de garde doit être programmable de 1 ms à 60 s.', 'Une fois activé, le chien de garde ne doit plus pouvoir être désactivé avant le prochain reset.', 'Un rafraîchissement hors de la fenêtre autorisée doit provoquer un reset.', 'La cause du dernier reset doit être lisible par le logiciel après le redémarrage.'],
    der: [[4, 'La cause du reset doit distinguer le chien de garde, la sous-tension et le reset logiciel.']] },
  { k: 'CRC', de: 'de l’unité CRC', nom: 'Unité CRC', blk: 'crc_engine', t: 'num', regs: [['POLY', 'VAL'], ['INIT', 'VAL'], ['DATA', 'IN'], ['RESULT', 'OUT'], ['CTRL', 'REFLECT']], sig: ['crc_valid', 'dma_req_crc'], api: ['crc_config', 'crc_feed', 'crc_result'],
    ev: ['l’écriture d’un mot dans DATA', 'un changement de polynôme', 'la fin d’un bloc reçu par DMA'],
    ers: ['L’unité CRC doit calculer les CRC-32 et CRC-16 CCITT.', 'L’unité CRC doit traiter un mot de 32 bits par cycle d’horloge.', 'La valeur initiale et le polynôme doivent être programmables.', 'L’unité CRC doit pouvoir être alimentée directement par le contrôleur DMA.'],
    der: [[0, 'Le calcul doit pouvoir reprendre à partir d’une valeur intermédiaire sauvegardée.']] },
  { k: 'CLK', de: 'des horloges et du reset', nom: 'Horloges et reset', blk: 'clk_rst', t: 'num', regs: [['CLKEN', 'GATE'], ['DIV', 'RATIO'], ['RSTCTL', 'SWRST'], ['CSS', 'FAIL'], ['FREQMON', 'COUNT']], sig: ['clk_io', 'rst_io_n', 'css_fail'], api: ['clk_enable', 'clk_set_div', 'periph_reset', 'clk_measure'],
    ev: ['la perte de l’horloge externe', 'un changement de diviseur', 'un reset logiciel de périphérique', 'la sortie du reset système'],
    ers: ['Chaque périphérique doit pouvoir être arrêté individuellement par coupure de son horloge.', 'Un reset logiciel par périphérique doit être disponible sans affecter les autres blocs.', 'Les diviseurs d’horloge doivent être modifiables sans glitch sur l’horloge produite.', 'Le système doit basculer automatiquement sur l’oscillateur interne si l’horloge externe disparaît.', 'La fréquence de chaque domaine d’horloge doit être mesurable par le logiciel.', 'Les horloges doivent être stables moins de 100 µs après la sortie du reset.'],
    der: [] },
  { k: 'PWR', de: 'de la gestion d’énergie', nom: 'Gestion d’énergie', blk: 'pwr_ctrl', t: 'num', regs: [['PWRCTL', 'SLEEP'], ['WAKE', 'SRC'], ['STATE', 'MODE'], ['UVMON', 'THRESH'], ['RET', 'EN']], sig: ['pwr_req', 'wake_irq', 'uv_alert'], api: ['pwr_sleep', 'pwr_wakeup', 'pwr_set_uv_threshold'],
    ev: ['une demande d’entrée en veille', 'un événement de réveil', 'une sous-tension détectée', 'la fin de la séquence de rétention'],
    ers: ['Le sous-système doit supporter un mode veille avec une consommation inférieure à 50 µA.', 'La sortie de veille doit être possible sur interruption UART, timer ou broche externe.', 'Le contexte des registres de configuration doit être conservé pendant la veille.', 'Le passage en veille doit être refusé tant qu’un transfert DMA est actif.', 'Le système doit être opérationnel moins de 20 µs après un événement de réveil.', 'La tension de chaque domaine doit être surveillée avec une alerte de sous-tension.'],
    der: [] },
  { k: 'SEC', de: 'de la protection des registres', nom: 'Protection des registres', blk: 'sec_guard', t: 'num', regs: [['LOCK', 'EN'], ['KEY', 'SEQ'], ['VIOL', 'ADDR'], ['DBGCTL', 'DISABLE']], sig: ['sec_viol', 'dbg_en'], api: ['sec_lock', 'sec_unlock', 'sec_read_violations'],
    ev: ['une écriture sur un registre verrouillé', 'une séquence de clé incorrecte', 'la désactivation du debug'],
    ers: ['Les registres de configuration critiques doivent pouvoir être verrouillés jusqu’au prochain reset.', 'Toute tentative d’écriture sur un registre verrouillé doit être journalisée et signalée.', 'Le déverrouillage doit exiger une séquence de clé en deux écritures.', 'L’accès de débogage doit pouvoir être désactivé de façon irréversible.'],
    der: [[1, 'Le journal des violations doit conserver au moins les 8 dernières adresses fautives.']] },
  { k: 'ADC', de: 'du convertisseur', nom: 'Convertisseur analogique-numérique', blk: 'adc_sar', t: 'ana', regs: [['SEQ', 'CHAN'], ['CTRL', 'TRIG'], ['DATA', 'RESULT'], ['SMPT', 'CYCLES']], sig: ['adc_eoc', 'irq_adc', 'adc_trig'], api: ['adc_config', 'adc_start_seq', 'adc_read'],
    ev: ['la fin d’une conversion', 'un déclenchement par timer', 'la fin d’une séquence'],
    par: [['ENOB', 'le nombre effectif de bits', 'est supérieur ou égal à 10,5 bits', 'pour un signal d’entrée jusqu’à 100 kHz', 'enob', '≥ 10,5 bits'], ['INL', 'la non-linéarité intégrale', 'reste inférieure à 2 LSB', 'sur toute la plage d’entrée', 'inl', '≤ 2 LSB'], ['IDD', 'la consommation', 'reste inférieure à 400 µA', 'à 1 Méch/s', 'idd', '≤ 400 µA'], ['TCONV', 'le temps de conversion', 'est inférieur à 1 µs', 'à 1,10 V et 125 °C', 'tconv', '≤ 1 µs']],
    ers: ['Le convertisseur doit fournir des résultats sur 12 bits à 1 million d’échantillons par seconde.', 'Le nombre effectif de bits doit être d’au moins 10,5 jusqu’à 100 kHz.', 'Le convertisseur doit offrir 8 voies multiplexées avec une séquence programmable.', 'Les conversions doivent pouvoir être déclenchées par un timer.', 'La plage d’entrée doit couvrir 0 à 1,8 V.', 'La consommation doit rester inférieure à 400 µA à pleine cadence.'],
    der: [[2, 'Chaque voie doit pouvoir avoir son propre temps d’échantillonnage.']] },
  { k: 'PLL', de: 'de la PLL', nom: 'PLL d’E/S', blk: 'pll_io', t: 'ana', regs: [['CFG', 'NDIV'], ['STATUS', 'LOCK'], ['CTRL', 'BYPASS']], sig: ['pll_lock', 'irq_pll_unlock'], api: ['pll_set_freq', 'pll_wait_lock'],
    ev: ['la perte du verrouillage', 'un changement de rapport de division', 'la sortie du mode contourné'],
    par: [['JIT', 'la gigue de période', 'reste inférieure à 20 ps rms', 'sur tout le domaine de fonctionnement', 'jitter_rms', '≤ 20 ps'], ['TLOCK', 'le temps de verrouillage', 'est inférieur à 50 µs', 'pour un saut de fréquence de 400 à 800 MHz', 'tlock', '≤ 50 µs'], ['IDD', 'la consommation', 'reste inférieure à 2 mA', 'à 800 MHz', 'idd', '≤ 2 mA']],
    ers: ['La PLL doit produire une fréquence de 400 à 800 MHz à partir d’un quartz de 24 MHz.', 'La gigue de période doit rester inférieure à 20 ps rms.', 'La PLL doit se verrouiller en moins de 50 µs.', 'La perte de verrouillage doit être signalée par une interruption.', 'La PLL doit consommer moins de 2 mA.'],
    der: [[0, 'Un changement de fréquence doit être possible sans repasser par l’oscillateur interne.']] },
  { k: 'LDO', de: 'du régulateur', nom: 'Régulateur LDO', blk: 'ldo_core', t: 'ana', regs: [['CTRL', 'EN'], ['TRIM', 'VOUT'], ['STATUS', 'OCP']], sig: ['ldo_pg', 'ldo_ocp'], api: ['ldo_enable', 'ldo_trim'],
    ev: ['une surintensité', 'l’activation du régulateur', 'un échelon de charge'],
    par: [['VOUT', 'la tension de sortie', 'reste entre 1,078 V et 1,122 V', 'pour un courant de charge de 0 à 50 mA', 'vout', '1,078 à 1,122 V'], ['PSRR', 'la réjection d’alimentation', 'est d’au moins 40 dB', 'à 1 MHz', 'psrr', '≥ 40 dB'], ['IQ', 'le courant de repos', 'reste inférieur à 35 µA', 'en veille', 'iq_sleep', '≤ 35 µA'], ['ILIM', 'la limitation de courant', 'intervient avant 120 mA', 'en court-circuit', 'ilim', '≤ 120 mA']],
    ers: ['Le régulateur doit fournir 1,10 V à ± 2 % pour un courant de 0 à 50 mA.', 'La réjection d’alimentation doit atteindre 40 dB à 1 MHz.', 'Le courant de repos en veille doit être inférieur à 35 µA.', 'Le courant de sortie doit être limité à 120 mA en cas de court-circuit.', 'Le démarrage progressif doit durer moins de 200 µs.'],
    der: [[0, 'La tension de sortie doit rester dans ± 5 % lors d’un échelon de charge de 25 mA.']] },
  { k: 'TSENS', de: 'du capteur de température', nom: 'Capteur de température', blk: 'tsens', t: 'ana', regs: [['CTRL', 'START'], ['DATA', 'TEMP'], ['ALARM', 'THRESH']], sig: ['tsens_done', 'irq_temp'], api: ['tsens_read', 'tsens_set_alarm'],
    ev: ['la fin d’une mesure', 'le dépassement du seuil d’alarme'],
    par: [['ACC', 'l’erreur de mesure', 'reste dans ± 2 °C', 'de -40 à 125 °C après calibration', 'accuracy', '± 2 °C'], ['TMEAS', 'la durée de mesure', 'est inférieure à 50 µs', 'à toutes les températures', 'tmeas', '≤ 50 µs']],
    ers: ['Le capteur doit mesurer la température de -40 à 125 °C avec une précision de ± 2 °C après calibration.', 'Une mesure doit durer moins de 50 µs.', 'Le dépassement d’un seuil programmable doit déclencher une interruption.', 'La température doit être lisible par le logiciel en degrés entiers signés.'],
    der: [] },
]
// Blocs ajoutés : écriture compacte. regs « REG.FIELD », signaux, fonctions du driver séparés par des espaces.
const B = (k, nom, de, blk, t, inst, regs, sig, api, ev, ers, par) => ({ k, nom, de, blk, t, inst, regs: regs.split(' ').map(x => x.split('.')), sig: sig.split(' '), api: api.split(' '), ev, ers, der: [], par })
const F_NEW = [
  B('CORE', 'Cœurs applicatifs', 'des cœurs applicatifs', 'cpu_cluster', 'num', 1, 'PWRCTL.CORE_ON RVBAR.ADDR CLUSTER.STATUS DBGPRSR.PU ERRSTATUS.SERR', 'core_wfi core_rst_n cluster_irq', 'cpu_on cpu_off cpu_suspend',
    ['la mise sous tension d’un cœur', 'une erreur ECC dans un cache', 'l’entrée en attente d’interruption', 'un reset à chaud d’un cœur'],
    ['La grappe doit comporter 4 cœurs applicatifs 64 bits cadencés jusqu’à 1,5 GHz.', 'Chaque cœur doit pouvoir être mis hors tension indépendamment des autres.', 'L’adresse de démarrage de chaque cœur doit être programmable avant sa mise sous tension.', 'Les caches de niveau 1 doivent être protégés par parité.', 'Un cœur en attente d’interruption doit consommer moins de 5 mW.', 'La cohérence des caches entre les 4 cœurs doit être assurée par le matériel.']),
  B('L2C', 'Cache de niveau 2', 'du cache de niveau 2', 'l2_cache', 'num', 1, 'CTRL.EN ECCSTAT.CE ECCSTAT.UE LOCKDOWN.WAY MAINT.OP', 'l2_ecc_irq l2_flush_done', 'l2_flush l2_invalidate l2_lock_way',
    ['une erreur ECC non corrigible', 'la fin d’un nettoyage complet', 'un conflit d’accès entre deux cœurs'],
    ['Le cache de niveau 2 doit avoir une capacité de 1 Mo partagée entre les 4 cœurs.', 'Une erreur ECC simple doit être corrigée sans intervention logicielle.', 'Une erreur ECC double doit déclencher une interruption dans les 20 cycles.', 'Des voies du cache doivent pouvoir être verrouillées pour du code temps réel.', 'Le nettoyage complet du cache doit pouvoir être demandé par une seule écriture de registre.', 'La latence d’un accès réussi doit être inférieure à 12 cycles.']),
  B('SMMU', 'Unité de traduction d’adresses', 'de l’unité de traduction d’adresses', 'smmu_top', 'num', 1, 'CR0.SMMUEN STRTAB.BASE GERROR.SFM TLBI.VA EVTQ.PROD', 'smmu_evt_irq smmu_gerr', 'smmu_attach smmu_map smmu_unmap',
    ['une faute de traduction', 'l’invalidation d’une entrée de TLB', 'le débordement de la file d’événements'],
    ['Les accès des maîtres DMA doivent être traduits et filtrés par une unité de traduction d’adresses.', 'Chaque maître doit pouvoir être associé à un contexte de traduction distinct.', 'Une faute de traduction doit être enregistrée avec l’adresse et l’identifiant du maître fautif.', 'Les pages de 4 Ko, 2 Mo et 1 Go doivent être supportées.', 'Une invalidation de TLB doit être terminée en moins de 2 µs.', 'Un maître non configuré doit être bloqué par défaut.']),
  B('NOC', 'Interconnexion principale', 'de l’interconnexion principale', 'noc_main', 'num', 1, 'QOS.PRIO QOS.BW TIMEOUT.CYCLES ERRLOG.ADDR PROBE.CNT', 'noc_err_irq noc_timeout', 'noc_set_qos noc_read_errlog',
    ['une transaction sans réponse', 'une erreur de décodage', 'la saturation d’un port'],
    ['L’interconnexion doit relier 12 maîtres et 24 esclaves avec une bande passante totale de 64 Go/s.', 'La qualité de service doit être réglable par maître avec 4 niveaux de priorité.', 'Une transaction sans réponse doit être terminée en erreur après un délai programmable.', 'Toute erreur de décodage d’adresse doit être journalisée avec l’adresse et le maître fautif.', 'Des sondes de performance doivent compter les transactions par port.', 'La latence d’un accès processeur vers la mémoire interne doit rester inférieure à 40 cycles.']),
  B('FWL', 'Pare-feu d’adresses', 'du pare-feu d’adresses', 'noc_firewall', 'num', 1, 'REGION.BASE REGION.LIMIT REGION.PERM VIOL.ADDR LOCK.EN', 'fw_viol_irq', 'fw_set_region fw_lock',
    ['un accès hors région autorisée', 'le verrouillage de la configuration', 'un accès non sécurisé à une région sécurisée'],
    ['Le pare-feu doit définir 32 régions d’adresses avec des droits de lecture et d’écriture par maître.', 'Un accès non autorisé doit être bloqué et renvoyer une erreur au maître.', 'Chaque violation doit être journalisée avec l’adresse, le maître et le type d’accès.', 'La configuration du pare-feu doit pouvoir être verrouillée jusqu’au prochain reset.', 'Les régions doivent pouvoir être marquées sécurisées ou non sécurisées.']),
  B('APB', 'Ponts périphériques', 'des ponts périphériques', 'apb_bridge', 'num', 3, 'CFG.TIMEOUT STATUS.PSLVERR CLKGATE.EN', 'pslverr pready', 'bridge_status',
    ['une réponse d’erreur d’un périphérique', 'un périphérique qui ne répond pas'],
    ['Les périphériques lents doivent être raccordés par des ponts APB à 100 MHz.', 'Une erreur renvoyée par un périphérique doit être propagée au maître d’origine.', 'Un périphérique qui ne répond pas doit provoquer une erreur après 256 cycles.', 'L’horloge de chaque pont doit être coupée automatiquement en l’absence d’accès.']),
  B('DDRC', 'Contrôleur DDR', 'du contrôleur DDR', 'ddr_ctrl', 'num', 1, 'MSTR.TYPE RFSHCTL.PERIOD ECCCFG.MODE ECCSTAT.CE DFIMISC.INIT PWRCTL.SELFREF', 'ddr_ecc_irq dfi_init_done ddr_selfref_ack', 'ddr_init ddr_train ddr_selfref_enter',
    ['une erreur ECC corrigée', 'l’entrée en auto-rafraîchissement', 'la fin de l’entraînement', 'une demande de rafraîchissement urgent'],
    ['Le contrôleur doit supporter la LPDDR4 jusqu’à 3 200 MT/s sur un bus de 32 bits.', 'Les données doivent être protégées par un ECC en ligne corrigeant une erreur par mot.', 'La mémoire doit pouvoir passer en auto-rafraîchissement pendant la veille.', 'Les rafraîchissements doivent être planifiés sans dépasser l’intervalle imposé par le standard.', 'La séquence d’entraînement doit se terminer en moins de 50 ms au démarrage.', 'La bande passante utile doit atteindre 80 % du débit théorique en lecture séquentielle.', 'Les erreurs corrigées doivent être comptées par rang et par banque.']),
  B('DPHY', 'PHY DDR', 'du PHY DDR', 'ddr_phy', 'ana', 1, 'ZQCAL.START VREF.TRIM DLL.LOCK RDLVL.DONE', 'phy_dll_lock phy_init_done', 'phy_calibrate phy_read_eye',
    ['la fin de la calibration ZQ', 'la perte de verrouillage de la DLL', 'la fin du réglage en lecture'],
    ['Le PHY doit atteindre 3 200 MT/s avec une ouverture d’œil d’au moins 0,35 UI.', 'La calibration d’impédance doit être refaite périodiquement sans interrompre le trafic.', 'Le PHY doit consommer moins de 120 mW à pleine vitesse.', 'Le réglage des délais en lecture et en écriture doit être automatique au démarrage.', 'Le PHY doit supporter une tension d’E/S de 1,1 V.'],
    [['EYE', 'l’ouverture de l’œil en lecture', 'dépasse 0,35 UI', 'à 3 200 MT/s', 'eye_rd', '≥ 0,35 UI'], ['ZQ', 'l’erreur d’impédance après calibration', 'reste dans ± 10 %', 'sur toute la plage de température', 'zq_err', '± 10 %'], ['JIT', 'la gigue de l’horloge DDR', 'reste inférieure à 25 ps crête à crête', 'à 1 600 MHz', 'ck_jitter', '≤ 25 ps'], ['PWR', 'la consommation', 'reste inférieure à 120 mW', 'à 3 200 MT/s', 'pwr', '≤ 120 mW']]),
  B('SRAM', 'Mémoire interne', 'de la mémoire interne', 'sram_ctrl', 'num', 4, 'ECCCFG.EN ECCSTAT.ADDR INIT.START RET.EN', 'sram_ecc_irq sram_init_done', 'sram_scrub sram_retain',
    ['une erreur ECC', 'la fin de l’initialisation', 'l’entrée en rétention'],
    ['Le SoC doit disposer de 2 Mo de mémoire interne accessible en un cycle par les cœurs.', 'La mémoire interne doit être protégée par ECC avec correction d’une erreur par mot.', 'La mémoire doit pouvoir être initialisée à zéro par le matériel au démarrage.', '512 Ko de mémoire interne doivent être conservés pendant la veille.', 'Un balayage périodique doit corriger les erreurs latentes.']),
  B('ROM', 'ROM de démarrage', 'de la ROM de démarrage', 'boot_rom', 'num', 1, 'BOOTCFG.SRC BOOTSTAT.STAGE PATCH.EN', 'rom_done', 'rom_boot rom_get_status',
    ['l’échec d’une source de démarrage', 'la fin du chargement', 'l’application d’un correctif'],
    ['Le code de démarrage doit résider dans une ROM de 128 Ko.', 'La ROM doit pouvoir démarrer depuis la QSPI, l’eMMC ou l’USB.', 'En cas d’échec d’une source, la ROM doit essayer la source suivante de la liste.', 'L’étape atteinte par le démarrage doit être lisible après un échec.', 'La ROM doit pouvoir être corrigée par des correctifs chargés depuis l’OTP.']),
  B('OTP', 'Mémoire OTP', 'de la mémoire OTP', 'otp_ctrl', 'num', 1, 'PROG.ADDR PROG.DATA READ.ADDR LOCK.ROW STATUS.ERR', 'otp_ready otp_err', 'otp_read otp_program otp_lock',
    ['une programmation', 'une erreur de lecture', 'le verrouillage d’une ligne'],
    ['Le SoC doit disposer de 16 Kbits de mémoire programmable une seule fois.', 'Chaque ligne d’OTP doit pouvoir être verrouillée en écriture.', 'Les données OTP doivent être protégées par un code correcteur.', 'Les zones contenant des clés ne doivent jamais être lisibles par le logiciel non sécurisé.', 'La programmation d’un mot doit durer moins de 100 µs.']),
  B('SBOOT', 'Démarrage sécurisé', 'du démarrage sécurisé', 'sboot_ctrl', 'num', 1, 'CFG.MODE STATUS.AUTH KEYSEL.IDX ANTIROLL.CNT', 'auth_ok auth_fail', 'sboot_verify sboot_get_status',
    ['l’échec d’une vérification de signature', 'l’incrément du compteur anti-retour', 'le passage en mode sécurisé'],
    ['Le premier code chargé doit être authentifié par une signature avant son exécution.', 'Une image dont la signature est invalide ne doit jamais être exécutée.', 'Un compteur anti-retour doit empêcher le chargement d’une version plus ancienne.', 'Jusqu’à 4 clés publiques doivent pouvoir être révoquées individuellement.', 'La vérification d’une image de 256 Ko doit durer moins de 30 ms.']),
  B('AES', 'Accélérateur AES', 'de l’accélérateur AES', 'aes_engine', 'num', 1, 'CTRL.MODE KEY.SEL IV.VAL STATUS.BUSY DMA.EN', 'aes_done aes_dma_req', 'aes_setkey aes_encrypt aes_decrypt',
    ['la fin d’un bloc', 'un changement de clé', 'une erreur de configuration'],
    ['L’accélérateur doit chiffrer en AES-128 et AES-256 dans les modes ECB, CBC, CTR et GCM.', 'Le débit de chiffrement doit atteindre 1 Gbit/s en AES-256 GCM.', 'Les clés doivent pouvoir être chargées depuis le stockage de clés sans transiter par le logiciel.', 'L’accélérateur doit être protégé contre les attaques par analyse simple de consommation.', 'L’accélérateur doit pouvoir être alimenté par DMA.']),
  B('SHA', 'Accélérateur de hachage', 'de l’accélérateur de hachage', 'sha_engine', 'num', 1, 'CTRL.ALGO DATA.IN DIGEST.OUT STATUS.DONE', 'sha_done', 'sha_init sha_update sha_final',
    ['la fin d’un bloc de 512 bits', 'la finalisation d’un condensat'],
    ['L’accélérateur doit calculer les condensats SHA-256 et SHA-512.', 'Le débit doit atteindre 800 Mbit/s en SHA-256.', 'Un calcul doit pouvoir être suspendu et repris à partir d’un état sauvegardé.', 'Le mode HMAC doit être supporté avec une clé issue du stockage de clés.']),
  B('TRNG', 'Générateur aléatoire', 'du générateur aléatoire', 'trng_core', 'num', 1, 'CTRL.EN HEALTH.STATUS DATA.OUT FIFO.LEVEL', 'trng_ready trng_health_fail', 'trng_read trng_selftest',
    ['l’échec d’un test de santé', 'le remplissage de la FIFO'],
    ['Le générateur doit fournir des nombres aléatoires conformes au profil NIST SP 800-90B.', 'Des tests de santé en continu doivent détecter une source d’entropie défaillante.', 'Le débit doit atteindre 10 Mbit/s de données conditionnées.', 'Une défaillance de la source doit bloquer la sortie et lever une alarme.']),
  B('KEYS', 'Stockage de clés', 'du stockage de clés', 'key_vault', 'num', 1, 'SLOT.SEL SLOT.LOCK SLOT.USAGE CLEAR.ALL', 'key_valid', 'kv_load kv_lock kv_clear',
    ['une tentative de lecture d’une clé', 'l’effacement d’urgence'],
    ['Le SoC doit stocker 16 clés de 256 bits inaccessibles en lecture par le logiciel.', 'Chaque clé doit être restreinte à un usage déclaré : chiffrement, signature ou dérivation.', 'Toutes les clés doivent pouvoir être effacées en moins de 1 µs sur détection d’intrusion.', 'Une clé verrouillée ne doit plus pouvoir être remplacée avant le prochain reset.']),
  B('USB', 'Contrôleur USB 2.0', 'du contrôleur USB', 'usb_otg', 'num', 1, 'DCTL.RUNSTOP DSTS.SPEED EPCTL.EN GINTSTS.SOF PHYCTL.SUSPEND', 'usb_irq usb_vbus_valid', 'usb_init usb_ep_queue usb_suspend',
    ['un début de trame', 'une mise en suspension par l’hôte', 'la détection de VBUS', 'une erreur CRC sur un paquet'],
    ['Le contrôleur doit supporter l’USB 2.0 haute vitesse en mode hôte et périphérique.', 'Le contrôleur doit gérer 8 points de terminaison bidirectionnels.', 'La mise en suspension doit réduire la consommation du contrôleur sous 500 µA.', 'La reprise après suspension doit respecter les délais de la norme USB 2.0.', 'Le contrôleur doit pouvoir servir de source de démarrage pour la ROM.']),
  B('ETH', 'Contrôleur Ethernet', 'du contrôleur Ethernet', 'eth_mac', 'num', 1, 'MACCR.SPEED DMACTL.START MTLQ.SIZE PTPCTL.EN MDIO.ADDR', 'eth_irq eth_pps', 'eth_open eth_xmit eth_ptp_adj',
    ['la réception d’une trame', 'une erreur de CRC', 'une impulsion PPS', 'le débordement d’une file de réception'],
    ['Le contrôleur doit supporter l’Ethernet 10/100/1000 Mbit/s en interface RGMII.', 'L’horodatage matériel des trames doit être conforme à IEEE 1588 avec une précision de 8 ns.', 'Le contrôleur doit gérer 4 files d’émission et 4 files de réception avec priorités.', 'Les sommes de contrôle IP, TCP et UDP doivent être calculées par le matériel.', 'Le réveil sur réception d’un paquet magique doit être supporté.']),
  B('CAN', 'Contrôleur CAN FD', 'du contrôleur CAN FD', 'canfd_core', 'num', 2, 'CCCR.INIT NBTP.BRP DBTP.DBRP RXF0S.FL ECR.TEC', 'can_tx can_rx can_irq', 'can_init can_send can_set_filter',
    ['une perte d’arbitrage', 'le passage en état bus-off', 'la réception d’une trame filtrée'],
    ['Le contrôleur doit supporter le CAN FD jusqu’à 5 Mbit/s en phase de données.', 'Le contrôleur doit offrir 64 filtres d’identifiants programmables.', 'Le passage en état bus-off doit être signalé et la reprise doit suivre la norme ISO 11898-1.', 'L’horodatage des trames reçues doit avoir une résolution de 1 µs.']),
  B('QSPI', 'Contrôleur QSPI', 'du contrôleur QSPI', 'qspi_ctrl', 'num', 1, 'CR.MODE CCR.INSTR AR.ADDR DLR.LEN SR.BUSY XIP.EN', 'qspi_sclk qspi_cs_n qspi_irq', 'qspi_read qspi_program qspi_erase',
    ['la fin d’un effacement', 'une lecture en exécution directe', 'un délai d’attente dépassé'],
    ['Le contrôleur doit lire une mémoire flash série en mode quadruple jusqu’à 133 MHz.', 'Le code doit pouvoir être exécuté directement depuis la flash avec un cache de lecture.', 'Les opérations d’effacement et de programmation doivent être supportées par le contrôleur.', 'Le contrôleur doit pouvoir servir de source de démarrage pour la ROM.']),
  B('SDIO', 'Contrôleur SD et eMMC', 'du contrôleur SD et eMMC', 'sdmmc_host', 'num', 2, 'CMD.INDEX ARG.VAL BLKSIZE.LEN STATUS.CMDDONE CLKCTL.DIV', 'sd_clk sd_cmd sd_irq', 'mmc_init mmc_read_blocks mmc_write_blocks',
    ['la fin d’une commande', 'une erreur CRC sur les données', 'l’insertion d’une carte'],
    ['Le contrôleur doit supporter l’eMMC 5.1 en mode HS200 sur un bus de 8 bits.', 'Le contrôleur doit supporter les cartes SD en mode SDR104.', 'Les transferts de blocs doivent se faire par DMA avec liste de descripteurs.', 'Le contrôleur doit pouvoir servir de source de démarrage pour la ROM.']),
  B('DVFS', 'Mise à l’échelle tension-fréquence', 'de la mise à l’échelle tension-fréquence', 'dvfs_ctrl', 'num', 1, 'OPP.SEL STATUS.BUSY VCTRL.TARGET', 'dvfs_done', 'dvfs_set_opp dvfs_get_opp',
    ['un changement de point de fonctionnement', 'l’atteinte de la tension cible'],
    ['La grappe processeur doit supporter 5 points de fonctionnement tension-fréquence.', 'Un changement de point de fonctionnement doit durer moins de 100 µs.', 'La tension doit être relevée avant toute hausse de fréquence et abaissée après toute baisse.', 'Un point de fonctionnement non qualifié ne doit pas pouvoir être sélectionné.']),
  B('RTC', 'Horloge temps réel', 'de l’horloge temps réel', 'rtc_core', 'num', 1, 'TIME.SEC ALARM.SEC CAL.PPM CTRL.EN', 'rtc_alarm_irq', 'rtc_set_time rtc_set_alarm',
    ['le déclenchement d’une alarme', 'une correction de calibration'],
    ['L’horloge temps réel doit rester active dans tous les modes de veille.', 'La dérive doit être corrigeable par logiciel avec une résolution de 1 ppm.', 'Une alarme doit pouvoir réveiller le système.', 'L’horloge temps réel doit consommer moins de 1 µA.']),
  B('BG', 'Référence de tension', 'de la référence de tension', 'bandgap', 'ana', 1, 'TRIM.VAL STATUS.READY', 'bg_ready', 'bg_trim',
    ['la mise sous tension', 'l’application de la calibration'],
    ['La référence de tension doit fournir 1,20 V à ± 0,5 % après calibration.', 'La dérive en température doit être inférieure à 20 ppm/°C.', 'La référence doit être établie moins de 30 µs après la mise sous tension.', 'La référence doit rester disponible en veille avec une consommation inférieure à 2 µA.'],
    [['VREF', 'la tension de référence', 'reste entre 1,194 V et 1,206 V', 'après calibration de -40 à 125 °C', 'vref', '1,194 à 1,206 V'], ['TC', 'la dérive en température', 'reste inférieure à 20 ppm/°C', 'de -40 à 125 °C', 'tc', '≤ 20 ppm/°C'], ['TSTART', 'le temps d’établissement', 'est inférieur à 30 µs', 'à la mise sous tension', 'tstart', '≤ 30 µs']]),
  B('POR', 'Détecteur de mise sous tension', 'du détecteur de mise sous tension', 'por_bor', 'ana', 1, 'BOR.THRESH STATUS.FLAG', 'por_n bor_flag', 'bor_set_threshold',
    ['une baisse de tension', 'la mise sous tension'],
    ['Le reset doit être maintenu tant que la tension cœur n’a pas atteint 0,9 V.', 'Une baisse de tension sous le seuil programmé doit provoquer un reset en moins de 2 µs.', 'Le seuil de baisse de tension doit être programmable entre 0,85 V et 1,0 V.', 'L’origine d’un reset par baisse de tension doit être enregistrée.'],
    [['VTH', 'le seuil de détection de baisse de tension', 'reste entre 0,88 V et 0,92 V', 'sur toute la plage de température', 'bor_vth', '0,88 à 0,92 V'], ['TDET', 'le temps de détection', 'est inférieur à 2 µs', 'pour une chute de 100 mV/µs', 'tdet', '≤ 2 µs']]),
  B('DAC', 'Convertisseur numérique-analogique', 'du convertisseur numérique-analogique', 'dac_core', 'ana', 1, 'DATA.VAL CTRL.EN TRIG.SRC', 'dac_trig', 'dac_write dac_config',
    ['un déclenchement par timer', 'l’écriture d’une nouvelle valeur'],
    ['Le convertisseur doit produire une tension de 0 à 1,8 V sur 12 bits.', 'Le temps d’établissement doit être inférieur à 1 µs pour un pas pleine échelle.', 'La mise à jour doit pouvoir être déclenchée par un timer.', 'La non-linéarité différentielle doit rester inférieure à 1 LSB.'],
    [['DNL', 'la non-linéarité différentielle', 'reste inférieure à 1 LSB', 'sur toute la plage de sortie', 'dnl', '≤ 1 LSB'], ['TSET', 'le temps d’établissement', 'est inférieur à 1 µs', 'pour un pas pleine échelle', 'tset', '≤ 1 µs'], ['IDD', 'la consommation', 'reste inférieure à 250 µA', 'à 1 Méch/s', 'idd', '≤ 250 µA']]),
  B('RCO', 'Oscillateur RC interne', 'de l’oscillateur RC', 'rc_osc', 'ana', 1, 'TRIM.COARSE TRIM.FINE STATUS.READY', 'rco_ready', 'rco_calibrate',
    ['la fin de la calibration', 'le démarrage de l’oscillateur'],
    ['L’oscillateur interne doit fournir 32 MHz à ± 1 % après calibration.', 'L’oscillateur doit démarrer en moins de 10 µs.', 'La calibration doit pouvoir être faite en fonctionnement à partir de l’horloge temps réel.', 'L’oscillateur doit consommer moins de 60 µA.'],
    [['FREQ', 'la fréquence', 'reste dans ± 1 % de 32 MHz', 'après calibration de -40 à 125 °C', 'freq', '± 1 %'], ['IDD', 'la consommation', 'reste inférieure à 60 µA', 'à 32 MHz', 'idd', '≤ 60 µA'], ['TSTART', 'le temps de démarrage', 'est inférieur à 10 µs', 'à froid', 'tstart', '≤ 10 µs']]),
  B('JTAG', 'Port de débogage', 'du port de débogage', 'dbg_port', 'num', 1, 'IDCODE.VAL AUTH.STATUS DP.CTRL', 'tck tms tdo', 'dbg_unlock',
    ['une demande d’authentification', 'la connexion d’une sonde'],
    ['Le SoC doit être accessible par JTAG et par SWD.', 'L’accès de débogage doit exiger une authentification par défi-réponse en production.', 'L’arrêt d’un cœur par le débogueur doit pouvoir arrêter les timers et le chien de garde.', 'L’identifiant du composant doit être lisible par JTAG.']),
  B('TRACE', 'Trace processeur', 'de la trace processeur', 'trace_unit', 'num', 1, 'CTRL.EN FUNNEL.PORT BUF.SIZE TS.EN', 'trace_clk trace_data', 'trace_start trace_stop',
    ['le remplissage du tampon de trace', 'l’arrêt du cœur tracé'],
    ['L’exécution des 4 cœurs doit pouvoir être tracée simultanément.', 'La trace doit pouvoir être stockée dans un tampon interne de 64 Ko ou exportée sur 4 broches.', 'Les traces doivent être horodatées avec une horloge commune.', 'La trace ne doit pas ralentir l’exécution des cœurs.']),
]
// Nombre d'instances des blocs de F_OLD (F_NEW le donne directement dans B(...)).
const INST = { DMA: 2, UART: 4, SPI: 3, I2C: 3, TMR: 2, GPIO: 4, LDO: 4, PLL: 3, TSENS: 2, ADC: 2 }
// Sous-systèmes : code (dans les IDs), nom affiché, blocs dans l'ordre d'affichage.
const SUBS = [
  { code: 'CPU', nom: 'Grappe processeur', blocks: ['CORE', 'L2C', 'SMMU'] },
  { code: 'NOC', nom: 'Interconnexion', blocks: ['NOC', 'FWL', 'APB'] },
  { code: 'MEM', nom: 'Mémoires', blocks: ['DDRC', 'DPHY', 'SRAM', 'ROM', 'OTP'] },
  { code: 'SEC', nom: 'Sécurité', blocks: ['SBOOT', 'AES', 'SHA', 'TRNG', 'KEYS', 'SEC'] },
  { code: 'IO', nom: 'Sous-système d’E/S', blocks: ['DMA', 'UART', 'SPI', 'I2C', 'CRC'] },
  { code: 'SYS', nom: 'Services système', blocks: ['TMR', 'IRQ', 'GPIO', 'WDT'] },
  { code: 'CON', nom: 'Connectivité', blocks: ['USB', 'ETH', 'CAN', 'QSPI', 'SDIO'] },
  { code: 'PWR', nom: 'Énergie et horloges', blocks: ['CLK', 'PWR', 'DVFS', 'RTC'] },
  { code: 'AMS', nom: 'Conversion et capteurs', blocks: ['ADC', 'DAC', 'TSENS'] },
  { code: 'ALIM', nom: 'Alimentations et références', blocks: ['PLL', 'LDO', 'BG', 'POR', 'RCO'] },
  { code: 'DBG', nom: 'Débogage', blocks: ['JTAG', 'TRACE'] },
]
/* ---------- gabarits de phrases ----------
 * W : noms de scénarios (deviennent des noms de tests). ctx(f) tire un vocabulaire au hasard dans le bloc f.
 * T[niveau] : liste de gabarits ; text() en choisit un et évite les doublons exacts (12 essais). */
const W = ['nominal', 'burst', 'abort', 'error', 'reset', 'stress', 'boundary', 'concurrent', 'wrap', 'overflow', 'timeout', 'lowpower', 'random', 'corner', 'backpressure', 'reconfig', 'idle', 'chained', 'priority', 'recovery']
const ctx = f => { const [reg, field] = pick(f.regs); return { f, reg, field, sig: pick(f.sig), api: pick(f.api), ev: pick(f.ev), w: pick(W), n: pick([2, 3, 4, 8, 12, 16, 32]), s: f.k.toLowerCase(), hex: int(0, 255).toString(16).toUpperCase().padStart(2, '0') } }
const T = {
  SDS_HW: [
    c => `Sur ${c.ev}, le bloc ${c.f.blk} positionne ${c.reg}.${c.field} et le maintient jusqu’à acquittement logiciel.`,
    c => `Le signal ${c.sig} est produit par ${c.f.blk} de façon synchrone à l’horloge du bloc, au plus ${c.n} cycles après ${c.ev}.`,
    c => `Le registre ${c.reg} est accessible en lecture et en écriture sur le bus APB ; ses bits réservés sont lus à zéro.`,
    c => `Une écriture dans ${c.reg} pendant que l’opération est en cours est ignorée et signalée dans le registre de statut.`,
    c => `${c.f.blk} comporte une machine d’état IDLE, ARMED, ACTIVE, ERROR ; tout état illégal ramène en IDLE.`,
    c => `La valeur de reset de ${c.reg}.${c.field} est 0x${c.hex} et place le bloc dans un état inactif sûr.`,
    c => `${c.f.blk} traite ${c.ev} sans perte même si l’événement suivant arrive au cycle d’après.`,
    c => `Le champ ${c.reg}.${c.field} ne prend effet qu’au début de l’opération suivante, jamais en cours d’opération.`,
  ],
  SDS_ANA: [
    c => `Le bloc ${c.f.blk} expose ses réglages dans ${c.reg}.${c.field} ; toute modification passe par une séquence d’arrêt et de redémarrage.`,
    c => `Le signal ${c.sig} indique au domaine numérique que ${c.f.blk} est prêt ; il est resynchronisé sur deux bascules.`,
    c => `Le domaine numérique ne lit ${c.reg} qu’une fois ${c.sig} actif, pour éviter de capturer une valeur en transition.`,
    c => `${c.f.blk} est alimenté par un domaine dédié, isolé du domaine numérique pendant la veille.`,
  ],
  SDS_FW: [
    c => `Le driver expose ${c.api}(), qui renvoie un code d’erreur explicite et ne bloque jamais plus de ${c.n} ms.`,
    c => `${c.api}() vérifie ses paramètres et renvoie -EINVAL sur toute valeur hors plage.`,
    c => `Le driver ${c.s} enregistre une routine sur ${c.sig} et traite ${c.ev} avant d’acquitter l’interruption.`,
    c => `L’initialisation du driver ${c.s} écrit ${c.reg} puis relit la valeur pour vérifier la configuration.`,
    c => `Le driver ${c.s} remonte ${c.ev} à l’application par un rappel enregistré à l’initialisation.`,
  ],
  DDS: [
    c => `Dans ${c.f.blk}, le compteur associé à ${c.reg}.${c.field} est codé sur ${c.n * 2} bits et sature à sa valeur maximale.`,
    c => `La logique qui produit ${c.sig} est décrite dans ${c.f.blk}_${c.w}.sv, avec un registre de sortie pour supprimer les aléas.`,
    c => `Le décodeur d’adresses de ${c.f.blk} place ${c.reg} à l’offset 0x${c.hex} et renvoie une erreur APB hors plage.`,
    c => `La transition vers l’état ERROR de ${c.f.blk} a lieu au plus ${c.n} cycles après ${c.ev}, sans état intermédiaire.`,
    c => `La synchronisation de ${c.sig} entre domaines d’horloge utilise une double bascule et un protocole requête-acquittement.`,
    c => `${c.f.blk} mémorise ${c.reg}.${c.field} dans une bascule à reset asynchrone, relâché de façon synchrone.`,
    c => `${c.f.blk} détecte ${c.ev} par un comparateur sur ${c.reg}.${c.field}, évalué à chaque cycle.`,
  ],
  FWS: [
    c => `${c.api}() écrit la configuration dans ${c.reg}, attend l’acquittement matériel et renvoie 0 en cas de succès.`,
    c => `En cas de dépassement de délai, ${c.api}() remet le bloc ${c.s} dans son état initial et renvoie -ETIMEDOUT.`,
    c => `La routine d’interruption de ${c.sig} lit le statut, l’acquitte, puis notifie la tâche cliente par sémaphore.`,
    c => `Les accès à ${c.reg} sont protégés par une section critique pour rendre ${c.api}() réentrante.`,
    c => `Le driver ${c.s} expose ses compteurs d’erreurs dans une structure de diagnostic consultable à tout moment.`,
    c => `${c.api}() refuse l’appel avec -EBUSY tant que le traitement de ${c.ev} n’est pas terminé.`,
  ],
  INST: [
    (c, i) => `L’instance ${c.s}${i} est cadencée par clk_${c.s}${i} et reliée à la source d’interruption ${20 + int(0, 90)} du contrôleur global.`,
    (c, i) => `L’instance ${c.s}${i} est placée à l’adresse 0x4${int(0, 9)}${(int(0, 255)).toString(16).toUpperCase().padStart(2, '0')}_0000 et protégée par la région ${int(1, 31)} du pare-feu.`,
    (c, i) => `L’instance ${c.s}${i} appartient au domaine d’alimentation ${pick(['PD_PER', 'PD_AON', 'PD_CORE', 'PD_CON'])} et se réinitialise avec son reset dédié.`,
  ],
  VP: [
    c => `Séquence ${c.s}_${c.w} : stimuli aléatoires contraints sur ${c.reg}, scoreboard sur ${c.sig}.`,
    c => `Le délai entre ${c.ev} et ${c.sig} ne dépasse jamais ${c.n} cycles.`,
    c => `Couverture croisée des valeurs de ${c.reg}.${c.field} et des états de la machine de ${c.f.blk}.`,
    c => `Test dirigé ${c.s}_${c.w} : reset, configuration, scénario ${c.w}, contrôle final de ${c.reg}.`,
    c => `Absence de blocage de la machine d’état de ${c.f.blk}, démontrée par vérification formelle.`,
    c => `Le scénario provoque ${c.ev} pendant chaque autre opération ${c.f.de}, sans perte ni corruption.`,
  ],
  FWT: [
    c => `Test unitaire de ${c.api}() avec ${c.reg} simulé : cas nominal, paramètres invalides, dépassement de délai.`,
    c => `Test d’intégration sur modèle virtuel : appel de ${c.api}() puis contrôle de ${c.sig}.`,
    c => `Couverture de code du driver ${c.s} sur l’ensemble de la suite de tests.`,
    c => `Injection d’erreur : ${c.reg} relu à une valeur inattendue, ${c.api}() doit renvoyer une erreur.`,
    c => `Test d’intégration : provoquer ${c.ev} en boucle pendant 10 minutes, sans fuite de ressource.`,
  ],
  VAL: [
    c => `Sur FPGA, mesurer le délai entre ${c.sig} et sa prise en compte par le logiciel ; critère inférieur à ${c.n} µs.`,
    c => `Sur silicium, provoquer ${c.ev} sur banc et contrôler les registres ${c.reg}.`,
    c => `Démonstration sur carte d’évaluation du scénario ${c.w} avec le driver ${c.s}.`,
    c => `Mesure en chambre climatique du comportement ${c.f.de} à -40 °C et 125 °C.`,
  ],
}
const used = new Set()
function text(kind, f) { for (let i = 0; i < 12; i++) { const t = pick(T[kind])(ctx(f)); if (!used.has(t)) { used.add(t); return t } } return pick(T[kind])(ctx(f)) }

/* ---------- graphe ----------
 * mk() crée un nœud interne { key, doc, f, sub, txt, sat: [clés parentes], metrics, goal, required, branch }.
 * Les liens pointent vers des clés internes (n0, n1…) ; ils sont convertis en IDs lisibles à la numérotation.
 * `refTo` : l'énoncé cite une autre exigence (rendu en nœud reqRef). `parts` : texte avant/après la citation. */
const ALL = F_OLD.concat(F_NEW)
const BY = Object.fromEntries(ALL.map(f => [f.k, f]))
SUBS.forEach(s => s.blocks.forEach(k => { BY[k].sub = s.code; BY[k].inst = BY[k].inst || INST[k] || 1 }))
const ORDERED = SUBS.flatMap(s => s.blocks.map(k => BY[k]))
let seq = 0
const nodes = []
const mk = (doc, f, txt, extra = {}) => { const n = { key: 'n' + seq++, doc, f, sub: f.sub, txt, sat: [], metrics: [], goal: 100, required: [], branch: 'NUM', ...extra }; nodes.push(n); return n }
// Formulations des exigences client dérivées génériques ; l'ID du parent est inséré entre les deux parties.
const DERIV = [
  ['Le comportement exigé par ', ' doit être garanti de -40 à 125 °C et sur toute la plage d’alimentation.'],
  ['Le respect de ', ' doit pouvoir être vérifié par un autotest logiciel au démarrage.'],
  ['Toute violation de ', ' doit être détectée et signalée au logiciel.'],
  ['L’exigence ', ' doit rester satisfaite après une sortie de veille, sans reconfiguration logicielle.'],
  ['La configuration nécessaire à ', ' doit pouvoir être verrouillée jusqu’au prochain reset.'],
  ['Les paramètres qui garantissent ', ' doivent figurer dans le manuel de référence du SoC.'],
]
const ers = [], roots = []
ORDERED.forEach(f => {
  const rs = f.ers.map(t => { const n = mk('ERS', f, t); ers.push(n); roots.push(n); return n })
  f.der.forEach(([i, t]) => ers.push(mk('ERS', f, t, { sat: [rs[i].key] })))
  rs.forEach((r, i) => {
    const nd = R() < 0.88 ? (R() < 0.5 ? 2 : 1) : 0
    const opts = DERIV.slice(); if (f.inst > 1) opts.push(['L’exigence ', ` doit être satisfaite à l’identique par les ${f.inst} instances ${f.de}.`])
    for (let j = 0; j < nd; j++) { const d = opts.splice(Math.floor(R() * opts.length), 1)[0]; ers.push(mk('ERS', f, '', { sat: [r.key], parts: d, refTo: r.key })) }
  })
})
// Plans requis par défaut, répartis de façon déterministe (ANA+VAL pour l'analogique, DV+VAL, DV+FW+VAL).
roots.forEach((n, i) => {
  if (n.f.t === 'ana' && i % 2 === 0) n.required = ['ANA', 'VAL']
  else if (i % 4 === 0) n.required = ['DV', 'VAL']
  else if (i % 11 === 3) n.required = ['DV', 'FW', 'VAL']
})
const untraced = new Set(roots.filter((n, i) => i % 37 === 5).map(n => n.key))
roots.filter(n => untraced.has(n.key)).forEach(n => { n.required = [] })
const traced = ers.filter(n => !untraced.has(n.key))

const sdsNum = [], sdsAna = [], sdsFw = []
const addSds = (p, fw) => {
  if (fw) { sdsFw.push(mk('SDS', p.f, text('SDS_FW', p.f), { sat: [p.key], branch: 'FW' })); return }
  if (p.f.t === 'ana') sdsAna.push(mk('SDS', p.f, text('SDS_ANA', p.f), { sat: [p.key], branch: 'ANA' }))
  else sdsNum.push(mk('SDS', p.f, text('SDS_HW', p.f), { sat: [p.key] }))
}
traced.forEach((n, i) => {
  addSds(n); if (R() < 0.5) addSds(n)
  if (i % 2 === 0 || n.required.includes('FW')) addSds(n, true)
})
ORDERED.forEach(f => { if (f.inst < 2) return; const r0 = roots.find(r => r.f === f && !untraced.has(r.key)); for (let i = 0; i < f.inst; i++) T.INST.slice(0, 2 + (i % 2)).forEach(tf => sdsNum.push(mk('SDS', f, tf(ctx(f), i), { sat: [r0.key] }))) })
sdsNum.slice().forEach((p, i) => { if (i % 14 === 3) sdsNum.push(mk('SDS', p.f, text('SDS_HW', p.f), { sat: [p.key], refTo: p.key })) })

const dds = []
sdsNum.forEach((s, i) => { const x = R(), n = i % 47 === 6 ? 0 : (x < 0.25 ? 1 : x < 0.7 ? 2 : 3); for (let j = 0; j < n; j++) dds.push(mk('DDS', s.f, text('DDS', s.f), { sat: [s.key] })) })
dds.slice().forEach((d, i) => { if (i % 20 === 7) dds.push(mk('DDS', d.f, text('DDS', d.f), { sat: [d.key] })) })

const parUsed = new Map()
const LEADS = ['', 'Au coin le plus défavorable, ', 'Avec les parasites extraits du layout, ', 'Sur toute la plage d’alimentation de 0,99 à 1,21 V, ', 'Après un vieillissement accéléré de 1 000 h à 125 °C, ', 'Pendant un échelon de charge, ', 'Pour chaque instance, ', 'Avec un bruit d’alimentation de 50 mV crête à crête, ']
const ans = []
const ansFor = s => { const list = s.f.par; const k = s.f.k; const i = (parUsed.get(k) || 0); parUsed.set(k, i + 1); const p = list[i % list.length]; const v = Math.floor(i / list.length); const lead = LEADS[v % LEADS.length]; const txt = `${lead}${lead ? p[1] : p[1][0].toUpperCase() + p[1].slice(1)} ${s.f.de} ${p[2]} ${p[3]}.`; ans.push(mk('ANS', s.f, txt, { sat: [s.key], branch: 'ANA', par: p, variant: v })) }
sdsAna.forEach(s => { for (let j = 0; j < 3; j++) ansFor(s) })

const fws = []
sdsFw.forEach(s => { for (let j = 0; j < 2; j++) fws.push(mk('FWS', s.f, text('FWS', s.f), { sat: [s.key], branch: 'FW' })) })

dds.forEach((d, i) => { if (i % 61 === 8) return; mk('VP', d.f, '', { sat: [d.key] }); if (R() < 0.8) mk('VP', d.f, '', { sat: [d.key] }) })
sdsNum.forEach((s, i) => { if (i % 9 === 2) mk('VP', s.f, '', { sat: [s.key] }) })
ans.forEach((a, i) => { if (i % 41 === 4) return; mk('ANV', a.f, '', { sat: [a.key], par: a.par, kind: 'spec', variant: a.variant }); if (R() < 0.3) mk('ANV', a.f, '', { sat: [a.key], par: a.par, kind: pick(['mc', 'model']), variant: a.variant + 3 }) })
fws.forEach((s, i) => { if (i % 53 === 7) return; mk('FWT', s.f, '', { sat: [s.key], branch: 'FW', goal: 85 }); if (R() < 0.5) mk('FWT', s.f, '', { sat: [s.key], branch: 'FW', goal: 85 }) })
roots.filter(n => n.required.includes('VAL')).forEach((n, i) => { if (i % 23 === 5) return; mk('VAL', n.f, '', { sat: [n.key] }); if (R() < 0.5) mk('VAL', n.f, '', { sat: [n.key] }) })
traced.forEach(n => { if (!n.required.includes('VAL') && R() < 0.6) mk('VAL', n.f, '', { sat: [n.key] }) })
sdsNum.forEach(s => { if (R() < 0.05) mk('VAL', s.f, '', { sat: [s.key] }) })

/* ---------- énoncés et métriques des plans ----------
 * Les noms de métriques reprennent le scénario ou la fonction cités dans l'énoncé (lisibilité).
 * Environ 1 item sur 97 reste sans métrique (statut « tracée »). */
const FAM = { VP: 'DV', ANV: 'ANA', FWT: 'FW', VAL: 'VAL' }
function metrics(fam, n) {
  const f = n.f, s = f.k.toLowerCase(), mw = n.txt.match(/(?:Séquence |dirigé )[a-z0-9]+_([a-z]+)/) || n.txt.match(/scénario ([a-z]+)/), w = () => (mw ? mw[1] : pick(W)), ma = n.txt.match(/(\w+)\(\)/), api = () => (ma ? ma[1] : pick(f.api))
  if (fam === 'DV') {
    if (/formelle/.test(n.txt)) return ['assert:a_' + s + '_fsm_' + w()]
    const m = ['test:' + s + '_' + w() + '_test']
    if (R() < 0.6) m.push('assert:a_' + s + '_' + pick(W))
    if (R() < 0.6) m.push('cover:' + s + '_cov.cg_' + pick(W))
    return m
  }
  if (fam === 'ANA') return [n.kind + ':' + (n.kind === 'model' ? f.blk + '_rnm' : f.blk + '_' + n.par[4])]
  if (fam === 'FW') { if (/Couverture de code/.test(n.txt)) return ['codecov:' + s + '_drv.c']; const m = ['utest:test_' + api() + '_' + w()]; if (R() < 0.5) m.push('itest:it_' + s + '_' + pick(W)); return m }
  if (/mesurer|Mesure/.test(n.txt)) return ['mesure:' + s + '_' + w()]
  if (/Démonstration/.test(n.txt)) return ['demo:demo_' + s + '_' + w()]
  return ['proc:VAL-PROC-' + String(int(100, 9999)).padStart(4, '0')]
}
const deArt = p => p.startsWith('le ') ? 'du ' + p.slice(3) : p.startsWith('les ') ? 'des ' + p.slice(4) : 'de ' + p
const SPECV = ['Simulation par coins', 'Simulation par coins sur la vue extraite', 'Balayage de l’alimentation de 0,99 à 1,21 V', 'Simulation après vieillissement', 'Simulation transitoire sur échelon de charge', 'Balayage en température de -40 à 125 °C', 'Simulation instance par instance', 'Simulation avec bruit d’alimentation']
const KINDTXT = { spec: (n) => `${SPECV[(n.variant || 0) % SPECV.length]} ${deArt(n.par[1])} ${n.f.de}, ${n.par[3]} ; critère ${n.par[5]}.`, mc: (n) => `Monte-Carlo sur 500 tirages ${deArt(n.par[1])} ${n.f.de} ; objectif Cpk ≥ 1,33.`, model: (n) => `Corrélation du modèle real-number ${n.f.de} avec la simulation transistor, ${n.par[3]} ; écart maximal 2 %.` }
nodes.filter(n => FAM[n.doc]).forEach((n, i) => {
  n.txt = n.doc === 'ANV' ? KINDTXT[n.kind](n) : text(n.doc, n.f)
  n.metrics = i % 97 === 6 ? [] : metrics(FAM[n.doc], n)
})

/* ---------- numérotation : niveau, sous-système, rang ----------
 * Ordre dans un document : par bloc (ordre de SUBS), puis pour le SDS par branche NUM, ANA, FW.
 * Deux exigences reçoivent ensuite un diagramme de démonstration (machine d'état Mermaid, chronogramme WaveDrom). */
const ORDER = ['ERS', 'SDS', 'DDS', 'ANS', 'FWS', 'VP', 'ANV', 'FWT', 'VAL']
const byKey = new Map(nodes.map(n => [n.key, n]))
const BR = ['NUM', 'ANA', 'FW']
const groups = new Map()
nodes.forEach(n => { const g = n.doc + '|' + n.sub; if (!groups.has(g)) groups.set(g, []); groups.get(g).push(n) })
const docNodes = (d, s) => { const list = groups.get(d + '|' + s) || [], out = []; SUBS.find(x => x.code === s).blocks.forEach(k => { const fl = list.filter(n => n.f.k === k); if (d === 'SDS') BR.forEach(b => out.push(...fl.filter(n => n.branch === b))); else out.push(...fl) }); return out }
ORDER.forEach(d => SUBS.forEach(s => docNodes(d, s.code).forEach((n, i) => { n.rid = `${d}-${s.code}-${String(i + 1).padStart(3, '0')}` })))
nodes.filter(n => n.parts).forEach(n => { n.txt = n.parts[0] + byKey.get(n.refTo).rid + n.parts[1] })

const sdsFsm = docNodes('SDS', 'IO')[0], ddsWave = docNodes('DDS', 'IO')[0]
sdsFsm.txt = 'Le bloc dma_top comporte une machine d’état IDLE, ARMED, ACTIVE, ERROR ; tout état illégal ramène en IDLE.'
sdsFsm.diagram = { lang: 'mermaid', src: 'stateDiagram-v2\n  [*] --> IDLE\n  IDLE --> ARMED: CTRL.EN = 1\n  ARMED --> IDLE: CTRL.EN = 0\n  ARMED --> ACTIVE: dma_req\n  ACTIVE --> IDLE: LEN = 0\n  ACTIVE --> ERROR: SLVERR ou DECERR\n  ERROR --> IDLE: STATUS.ERRACK' }
ddsWave.txt = 'Sur réponse SLVERR, irq_err monte un cycle après hresp et reste haut jusqu’à l’écriture de STATUS.ERRACK.'
ddsWave.diagram = { lang: 'wavedrom', src: JSON.stringify({ signal: [{ name: 'clk', wave: 'p........' }, { name: 'hready', wave: '1.0.1....' }, { name: 'hresp', wave: '0..1.0...', node: '...a.....' }, { name: 'irq_err', wave: '0...1..0.', node: '....b..d.' }, { name: 'ERRACK (écriture)', wave: '0.....10.', node: '......c..' }], edge: ['a~>b 1 cycle', 'c~>d'], head: { text: 'Signalement d’une erreur esclave' } }, null, 1) }

/* ---------- JSON Tiptap ----------
 * Format consommé tel quel par l'éditeur (nœuds requirement, reqRef, diagram, table…). */
const P = (...content) => ({ type: 'paragraph', content: content.filter(Boolean).map(c => typeof c === 'string' ? { type: 'text', text: c } : c) })
const H = (level, t) => ({ type: 'heading', attrs: { level }, content: [{ type: 'text', text: t }] })
const RF = k => ({ type: 'reqRef', attrs: { rid: byKey.get(k).rid } })
const REQ = n => ({ type: 'requirement', attrs: { rid: n.rid, satisfies: n.sat.map(k => byKey.get(k).rid), metrics: n.metrics, goal: n.goal, required: n.required },
  content: [n.parts ? P(n.parts[0], RF(n.refTo), n.parts[1]) : n.refTo ? P(n.txt.replace(/\.$/, '') + ', en complément de ', RF(n.refTo), '.') : P(n.txt), ...(n.diagram ? [{ type: 'diagram', attrs: n.diagram }] : [])] })
const cell = (t, h) => ({ type: h ? 'tableHeader' : 'tableCell', content: [P(t)] })
const regTable = f => ({ type: 'table', content: [['Registre', 'Champ', 'Offset', 'Accès'], ...f.regs.map(([r, fl], i) => [r, fl, '0x' + (i * 4).toString(16).toUpperCase().padStart(2, '0'), i % 3 === 2 ? 'RO' : 'RW'])].map((row, ri) => ({ type: 'tableRow', content: row.map(t => cell(t, ri === 0)) })) })
const META = {
  ERS: ['Exigences client', 'Extrait de la spécification client, révision D. Les exigences dérivées précisent une exigence client sans en changer le périmètre.'],
  SDS: ['SDS', 'Spécification de conception, branches numérique, analogique et logicielle.'],
  DDS: ['DDS', 'Conception détaillée des blocs numériques.'],
  ANS: ['Spécification analogique', 'Performances des blocs analogiques et conditions dans lesquelles elles sont garanties.'],
  FWS: ['Spécification FW', 'Comportement des drivers : API, séquences d’initialisation, gestion d’erreurs.'],
  VP: ['vPlan DV', 'Items de vérification en simulation et en formel, avec leurs métriques vManager.'],
  ANV: ['Plan de vérification analogique', 'Simulations par coins, Monte-Carlo et corrélation des modèles, exportées depuis ADE.'],
  FWT: ['Plan de test FW', 'Tests unitaires, tests d’intégration sur modèle virtuel et couverture de code des drivers.'],
  VAL: ['Plan de validation', 'Validation sur FPGA, carte d’évaluation et silicium.'],
}
const BRT = { NUM: 'Matériel numérique', ANA: 'Analogique', FW: 'Logiciel' }
function buildDoc(d, s) {
  const S = SUBS.find(x => x.code === s)
  const content = [H(1, `${META[d][0]} · ${S.nom}`), P(META[d][1])]
  const list = docNodes(d, s)
  S.blocks.forEach(k => {
    const f = BY[k]; const fl = list.filter(n => n.f === f); if (!fl.length) return
    content.push(H(2, f.nom))
    if (d === 'SDS') BR.forEach(b => { const bl = fl.filter(n => n.branch === b); if (!bl.length) return; content.push(H(3, BRT[b])); if (b === 'NUM' && f.k === 'DMA') content.push(regTable(f)); bl.forEach(n => content.push(REQ(n))) })
    else fl.forEach(n => content.push(REQ(n)))
  })
  return { type: 'doc', content }
}
/* ---------- résultats ----------
 * Format d'un résultat, par type de métrique (c'est le contrat lu par evalMetric dans app.js) :
 *   test/utest/itest : { pass, fail }        assert : { ok }         cover/codecov : { pct }
 *   spec  : { ok, corner, margin (%), view: 'post-layout' | 'schéma' }
 *   mc    : { cpk, n }                       model  : { err (%) }
 *   mesure: { val, min, max, unit, stale?, pending? }    proc/demo : { ok, stale?, pending? }
 * Une métrique absente de `results` = « absente des résultats ».
 * snap 'a' (3 octobre) a des taux d'échec plus élevés que 'b' (4 octobre). */
const CORNERS = ['tt · 1,10 V · 25 °C', 'ss · 0,99 V · 125 °C', 'ss · 0,99 V · -40 °C', 'ff · 1,21 V · 125 °C', 'ff · 1,21 V · -40 °C']
function result(m, snap) {
  const h = hash(m + '#'), h2 = hash(m + '@'), [kind] = m.split(':')
  const bad = snap === 'a' ? 0.05 : 0.005
  if (h > (snap === 'a' ? 0.985 : 0.997)) return null
  if (kind === 'test' || kind === 'utest' || kind === 'itest') { const tot = int(4, 60); return h < bad ? { pass: tot - 1 - Math.floor(h2 * 3), fail: 1 + Math.floor(h2 * 3) } : { pass: tot, fail: 0 } }
  if (kind === 'assert') return { ok: h >= bad * 0.7 }
  if (kind === 'cover') return { pct: h < (snap === 'a' ? 0.1 : 0.02) ? 72 + Math.floor(h2 * 26) : 100 }
  if (kind === 'codecov') return { pct: h < (snap === 'a' ? 0.15 : 0.04) ? 70 + Math.floor(h2 * 14) : 86 + Math.floor(h2 * 13) }
  if (kind === 'spec') { const fail = h < (snap === 'a' ? 0.06 : 0.012); return { ok: !fail, corner: CORNERS[Math.floor(h2 * CORNERS.length)], margin: fail ? -Math.round(2 + h2 * 8) : Math.round(4 + h2 * 30), view: h > 0.975 ? 'schéma' : 'post-layout' } }
  if (kind === 'mc') { const cpk = +(snap === 'a' ? 1.2 + h2 * 0.5 : 1.31 + h2 * 0.5).toFixed(2); return { cpk, n: 500 } }
  if (kind === 'model') return { err: +(0.4 + h2 * (snap === 'a' ? 1.9 : 1.62)).toFixed(1) }
  const st = { stale: h > 0.27 && h < 0.276 && snap === 'b', pending: h > 0.2 && h < 0.21 }
  if (kind === 'mesure') { const max = pick([5, 10, 20, 50]); return { ...st, unit: 'µs', min: 0, max, val: +(h < bad ? max * (1.1 + h2 * 0.4) : max * (0.3 + h2 * 0.6)).toFixed(1) } }
  return { ...st, ok: h >= bad }
}
const allMetrics = [...new Set(nodes.flatMap(n => n.metrics))]
const mkSession = (snap, label, ids) => ({ label, ids, results: Object.fromEntries(allMetrics.map(m => [m, result(m, snap)]).filter(([, r]) => r)) })
export const SESSIONS = {
  n1003: mkSession('a', 'Résultats du 3 octobre', { DV: 'reg_nightly_20261003_0215', ANA: 'Campagne ADE-13, post-layout', FW: 'fw-ci #1482 (a91c3e2)', VAL: 'Campagne VAL-07, FPGA rev B' }),
  n1004: mkSession('b', 'Résultats du 4 octobre', { DV: 'reg_nightly_20261004_0215', ANA: 'Campagne ADE-14, post-layout', FW: 'fw-ci #1490 (4f0d7b9)', VAL: 'Campagne VAL-08, silicium A0' }),
}
export function seedDocs() { const o = {}; ORDER.forEach(d => SUBS.forEach(s => { o[d + '|' + s.code] = buildDoc(d, s.code) })); return o }
export const SUB_LIST = SUBS.map(s => ({ code: s.code, nom: s.nom }))
export const TOTAL = nodes.length
