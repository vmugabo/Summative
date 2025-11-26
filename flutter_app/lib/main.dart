import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Life Expectancy Predictor',
      theme: ThemeData(primarySwatch: Colors.indigo),
      home: const PredictorPage(),
    );
  }
}

class PredictorPage extends StatefulWidget {
  const PredictorPage({Key? key}) : super(key: key);

  @override
  State<PredictorPage> createState() => _PredictorPageState();
}

class _PredictorPageState extends State<PredictorPage> {
  // Feature list from the model metadata
  final List<String> features = const [
    "Adult_mortality",
    "Under_five_deaths",
    "Infant_deaths",
    "Schooling",
    "Polio",
    "Diphtheria",
    "BMI",
    "GDP_per_capita",
    "Incidents_HIV",
    "Economy_status_Developed",
    "Economy_status_Developing",
    "Measles",
    "Thinness_ten_nineteen_years",
    "Thinness_five_nine_years",
    "Hepatitis_B",
  ];

  // Validation ranges computed from the dataset
  final Map<String, List<double>> ranges = {
    "Adult_mortality": [49.384, 719.3605],
    "Under_five_deaths": [2.3, 224.9],
    "Infant_deaths": [1.8, 138.1],
    "Schooling": [1.1, 14.1],
    "Polio": [8.0, 99.0],
    "Diphtheria": [16.0, 99.0],
    "BMI": [19.8, 32.1],
    "GDP_per_capita": [148.0, 112418.0],
    "Incidents_HIV": [0.01, 21.68],
    "Economy_status_Developed": [0.0, 1.0],
    "Economy_status_Developing": [0.0, 1.0],
    "Measles": [10.0, 99.0],
    "Thinness_ten_nineteen_years": [0.1, 27.7],
    "Thinness_five_nine_years": [0.1, 28.6],
    "Hepatitis_B": [12.0, 99.0],
  };

  // Controllers for text fields (only for numeric features)
  late final Map<String, TextEditingController> controllers;

  // Toggles for economy one-hot features (use switches instead of numeric inputs)
  bool economyDeveloped = false;
  bool economyDeveloping = true;

  // Friendly label overrides for the UI
  final Map<String, String> labelOverrides = {
    "Adult_mortality": 'Adult mortality',
    "Under_five_deaths": 'Under-five deaths',
    "Infant_deaths": 'Infant deaths',
    "Schooling": 'Schooling (years)',
    "Polio": 'Polio coverage (%)',
    "Diphtheria": 'Diphtheria coverage (%)',
    "BMI": 'BMI',
    "GDP_per_capita": 'GDP per capita (USD)',
    "Incidents_HIV": 'HIV incidence (%)',
    "Economy_status_Developed": 'Economy: Developed',
    "Economy_status_Developing": 'Economy: Developing',
    "Measles": 'Measles (cases)',
    "Thinness_ten_nineteen_years": 'Thinness (10–19 yrs)',
    "Thinness_five_nine_years": 'Thinness (5–9 yrs)',
    "Hepatitis_B": 'Hepatitis B coverage (%)',
  };

  String prettyLabel(String key) {
    if (labelOverrides.containsKey(key)) return labelOverrides[key]!;
    // Fallback: replace underscores with spaces and title-case words
    final words = key.replaceAll('_', ' ').split(' ');
    return words
        .map((w) => w.isEmpty ? w : '${w[0].toUpperCase()}${w.substring(1)}')
        .join(' ');
  }

  // API endpoint: use local API when running in debug, hosted endpoint in release
  String apiUrl = kReleaseMode
      ? 'https://ml-summative.web.app/api/predict'
      : 'http://127.0.0.1:8000/predict';

  String resultText = '';
  bool loading = false;

  @override
  void initState() {
    super.initState();
    controllers = {
      for (var key in features)
        if (key != 'Economy_status_Developed' &&
            key != 'Economy_status_Developing')
          key: TextEditingController()
    };
  }

  @override
  void dispose() {
    for (final c in controllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  void showMessage(String text) {
    setState(() {
      resultText = text;
      loading = false;
    });
  }

  Future<void> showPredictionDialog(String text) async {
    setState(() => loading = false);
    await showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Prediction Result'),
        content: Text(text),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('OK'),
          ),
        ],
      ),
    );
    // Keep a short summary visible in the UI as well
    setState(() => resultText = text);
  }

  Future<void> predict() async {
    // Validate inputs
    final Map<String, dynamic> payload = {};
    for (var i = 0; i < features.length; i++) {
      final key = features[i];
      // handle economy toggles explicitly
      if (key == 'Economy_status_Developed') {
        payload[key] = economyDeveloped ? 1.0 : 0.0;
        continue;
      }
      if (key == 'Economy_status_Developing') {
        payload[key] = economyDeveloping ? 1.0 : 0.0;
        continue;
      }
      final text = controllers[key]?.text.trim() ?? '';
      if (text.isEmpty) {
        final msg = 'Missing value for $key';
        ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(msg), backgroundColor: Colors.red.shade700));
        setState(() => resultText = msg);
        return;
      }
      final value = double.tryParse(text.replaceAll(',', ''));
      if (value == null) {
        final msg = 'Invalid number for $key';
        ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(msg), backgroundColor: Colors.red.shade700));
        setState(() => resultText = msg);
        return;
      }
      // No strict range validation — inputs are flexible.
      // (Ranges are retained as informational data but not enforced.)
      payload[key] = value;
    }

    setState(() {
      loading = true;
      resultText = '';
    });

    try {
      final resp = await http
          .post(Uri.parse(apiUrl),
              headers: {'Content-Type': 'application/json'},
              body: jsonEncode(payload))
          .timeout(const Duration(seconds: 10));
      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body);
        final pred = data['prediction'] ??
            data['predicted_value'] ??
            data['result'] ??
            data;
        final modelName = (data is Map && data.containsKey('model'))
            ? data['model']
            : 'model';
        await showPredictionDialog(
            'Prediction: ${pred.toString()}\nModel: $modelName');
      } else {
        final err =
            'API error: ${resp.statusCode} ${resp.reasonPhrase}\n${resp.body}';
        // show as dialog for visibility
        await showPredictionDialog(err);
      }
    } catch (e) {
      showMessage('Request failed: $e');
    }
  }

  // Fill the form with a friendly default payload for testing
  void fillDefaults() {
    final Map<String, String> defaults = {
      "Adult_mortality": '100',
      "Under_five_deaths": '10',
      "Infant_deaths": '5',
      "Schooling": '8',
      "Polio": '90',
      "Diphtheria": '90',
      "BMI": '25',
      "GDP_per_capita": '5000',
      "Incidents_HIV": '0.1',
      "Measles": '20',
      "Thinness_ten_nineteen_years": '5',
      "Thinness_five_nine_years": '5',
      "Hepatitis_B": '80',
    };
    for (final key in features) {
      if (key == 'Economy_status_Developed' ||
          key == 'Economy_status_Developing') {
        continue;
      }
      controllers[key]?.text = defaults[key] ?? '';
    }
    setState(() {
      economyDeveloped = false;
      economyDeveloping = true;
      resultText = '';
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Life Expectancy Predictor')),
      body: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(
          children: [
            // Endpoint field
            Row(
              children: [
                const Text('Endpoint:'),
                const SizedBox(width: 8),
                Expanded(
                  child: TextFormField(
                    initialValue: apiUrl,
                    onChanged: (v) => apiUrl = v.trim(),
                    decoration: const InputDecoration(
                        border: OutlineInputBorder(), isDense: true),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            // Inputs
            Expanded(
              child: SingleChildScrollView(
                child: Column(
                  children: List.generate(features.length, (i) {
                    final key = features[i];
                    // Render switches for the economy one-hot features
                    if (key == 'Economy_status_Developed') {
                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 6.0),
                        child: SwitchListTile(
                          title: Text(prettyLabel(key)),
                          value: economyDeveloped,
                          onChanged: (v) =>
                              setState(() => economyDeveloped = v),
                        ),
                      );
                    }
                    if (key == 'Economy_status_Developing') {
                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 6.0),
                        child: SwitchListTile(
                          title: Text(prettyLabel(key)),
                          value: economyDeveloping,
                          onChanged: (v) =>
                              setState(() => economyDeveloping = v),
                        ),
                      );
                    }
                    // Default numeric input
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 6.0),
                      child: TextFormField(
                        controller: controllers[key],
                        keyboardType: const TextInputType.numberWithOptions(
                            decimal: true, signed: false),
                        decoration: InputDecoration(
                          labelText: prettyLabel(key),
                          hintText: 'Enter numeric value',
                          border: const OutlineInputBorder(),
                          isDense: true,
                        ),
                      ),
                    );
                  }),
                ),
              ),
            ),
            const SizedBox(height: 8),
            // Predict button and result
            SizedBox(
              width: double.infinity,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  ElevatedButton(
                    onPressed: loading ? null : predict,
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 14.0),
                      child: loading
                          ? const CircularProgressIndicator(color: Colors.white)
                          : const Text('Predict'),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                        border: Border.all(color: Colors.grey.shade300),
                        borderRadius: BorderRadius.circular(6)),
                    child: Text(resultText.isEmpty
                        ? 'Enter values and press Predict'
                        : resultText),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
