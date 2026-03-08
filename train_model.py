import sys
print("Starting script...", flush=True)

try:
    import numpy as np
    print("Imported numpy", flush=True)
    import pickle
    print("Imported pickle", flush=True)
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, Dropout
    from tensorflow.keras.optimizers import SGD
    print("Imported tensorflow", flush=True)
except Exception as e:
    print(f"Import Error: {e}", flush=True)
    sys.exit(1)

try:    
    # 1. Load the preprocessed data
    data = pickle.load(open("data.pickle", "rb"))
    train_x = np.array(data['train_x'])
    train_y = np.array(data['train_y'])

    # 2. Build the Model Architecture
    model = Sequential()
    model.add(Dense(128, input_shape=(len(train_x[0]),), activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(64, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(len(train_y[0]), activation='softmax'))

    # 3. Compile the model
    # Using Stochastic Gradient Descent (SGD) for stable convergence
    sgd = SGD(learning_rate=0.01, decay=1e-6, momentum=0.9, nesterov=True)
    model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])

    # 4. Train and Save
    # 200 epochs is usually sufficient for small intent datasets
    hist = model.fit(train_x, train_y, epochs=200, batch_size=5, verbose=1)
    model.save('campus_ai_model.h5', hist)

    print("Model trained and saved as campus_ai_model.h5", flush=True)

except Exception as e:
    print(f"Runtime Error: {e}", flush=True)
    import traceback
    traceback.print_exc()